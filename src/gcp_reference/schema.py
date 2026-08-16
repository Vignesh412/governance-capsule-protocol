"""JSON Schema validation API for GCP wire artifacts."""

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .errors import ErrorCode, GCPError


class SchemaValidator:
    """Load a schema bundle once and return deterministic validation errors."""

    def __init__(self, schema_dir: Path) -> None:
        self.schema_dir = Path(schema_dir)
        documents: Dict[str, dict] = {}
        for path in sorted(self.schema_dir.glob("*.json")):
            documents[path.name] = json.loads(path.read_text(encoding="utf-8"))
        if not documents:
            raise GCPError(
                ErrorCode.UNSUPPORTED_SEMANTICS,
                "No GCP schemas were found",
                {"schema_dir": str(self.schema_dir)},
            )
        registry = Registry()
        for document in documents.values():
            Draft202012Validator.check_schema(document)
            registry = registry.with_resource(
                document["$id"], Resource.from_contents(document)
            )
        self._documents = documents
        self._registry = registry
        self._validators: Dict[str, Draft202012Validator] = {}

    @classmethod
    def project_default(cls) -> "SchemaValidator":
        """Load the schema directory from a source checkout."""

        return cls(Path(__file__).resolve().parents[2] / "schema")

    def validate(self, artifact: Mapping[str, Any], schema_name: str) -> None:
        try:
            schema = self._documents[schema_name]
        except KeyError as exc:
            raise GCPError(
                ErrorCode.UNSUPPORTED_SEMANTICS,
                "Unknown GCP schema",
                {"schema": schema_name},
            ) from exc
        validator = self._validators.setdefault(
            schema_name,
            Draft202012Validator(
                schema,
                registry=self._registry,
                format_checker=FormatChecker(),
            ),
        )
        errors = sorted(
            validator.iter_errors(artifact),
            key=lambda error: (list(error.absolute_path), error.message),
        )
        if not errors:
            return
        formatted = [
            {
                "path": "/" + "/".join(str(part) for part in error.absolute_path),
                "message": error.message,
            }
            for error in errors
        ]
        raise GCPError(
            ErrorCode.SCHEMA_INVALID,
            "Artifact does not conform to its GCP schema",
            {"schema": schema_name, "errors": formatted},
        )


_default_validator: Optional[SchemaValidator] = None


def validate_structure(artifact: Mapping[str, Any], schema_name: str) -> None:
    """Validate against the schema bundle in this source checkout."""

    global _default_validator
    if _default_validator is None:
        _default_validator = SchemaValidator.project_default()
    _default_validator.validate(artifact, schema_name)

#!/usr/bin/env python3
"""Validate GCP schemas and structural example fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"

VALID_FIXTURES = {
    "root-capsule.json": "capsule.schema.json",
    "child-capsule.json": "capsule.schema.json",
    "delegation-proof.json": "delegation-proof.schema.json",
    "approval.json": "approval.schema.json",
    "amendment.json": "amendment.schema.json",
    "revocation.json": "revocation.schema.json",
    "enforcement-receipt.json": "enforcement-receipt.schema.json",
    "completion-receipt.json": "lifecycle-receipt.schema.json",
    "rejection-receipt.json": "lifecycle-receipt.schema.json",
}

INVALID_FIXTURES = {
    "root-with-parent.json": "capsule.schema.json",
    "bounded-stale-without-window.json": "capsule.schema.json",
}


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def validator_for(schema_name: str) -> Draft202012Validator:
    schemas = {path.name: load(path) for path in SCHEMA_DIR.glob("*.json")}
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)

    schema = schemas[schema_name]
    registry = Registry()
    for document in schemas.values():
        registry = registry.with_resource(
            document["$id"], Resource.from_contents(document)
        )
    return Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )


def format_error(error) -> str:
    location = "/" + "/".join(str(part) for part in error.absolute_path)
    return f"{location}: {error.message}"


def main() -> int:
    failures: list[str] = []
    cache: dict[str, Draft202012Validator] = {}

    for fixture_name, schema_name in VALID_FIXTURES.items():
        validator = cache.setdefault(schema_name, validator_for(schema_name))
        errors = sorted(
            validator.iter_errors(load(ROOT / "examples" / "valid" / fixture_name)),
            key=lambda error: list(error.absolute_path),
        )
        if errors:
            failures.append(
                f"expected valid: {fixture_name}: "
                + "; ".join(format_error(error) for error in errors)
            )
        else:
            print(f"PASS valid   {fixture_name} -> {schema_name}")

    for fixture_name, schema_name in INVALID_FIXTURES.items():
        validator = cache.setdefault(schema_name, validator_for(schema_name))
        errors = list(
            validator.iter_errors(load(ROOT / "examples" / "invalid" / fixture_name))
        )
        if not errors:
            failures.append(f"expected invalid: {fixture_name} unexpectedly validated")
        else:
            print(f"PASS invalid {fixture_name} rejected by {schema_name}")

    semantic_fixtures = sorted((ROOT / "examples" / "semantic-invalid").glob("*.json"))
    for fixture in semantic_fixtures:
        document = load(fixture)
        if "expected_semantic_error" not in document:
            failures.append(f"semantic fixture lacks expected error: {fixture.name}")
        else:
            print(
                f"PASS semantic-manifest {fixture.name} -> "
                f"{document['expected_semantic_error']}"
            )

    if failures:
        print("\nFAILURES")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        f"\nValidated {len(VALID_FIXTURES)} valid fixtures, "
        f"{len(INVALID_FIXTURES)} invalid fixtures, and "
        f"{len(semantic_fixtures)} semantic-invalid manifests."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

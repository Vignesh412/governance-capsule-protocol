"""RFC 8785-style canonical JSON for the GCP v0.1 data domain."""

import json
import math
from typing import Any

from .errors import ErrorCode, GCPError


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16be", errors="surrogatepass")


def _validate(value: Any) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GCPError(ErrorCode.UNSUPPORTED_SEMANTICS, "Non-finite JSON number")
        raise GCPError(
            ErrorCode.UNSUPPORTED_SEMANTICS,
            "Floating-point JSON values are outside the GCP v0.1 canonical domain",
        )
    if isinstance(value, list):
        for item in value:
            _validate(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise GCPError(ErrorCode.UNSUPPORTED_SEMANTICS, "JSON object key is not a string")
            _validate(item)
        return
    raise GCPError(
        ErrorCode.UNSUPPORTED_SEMANTICS,
        "Value is outside the JSON data model",
        {"python_type": type(value).__name__},
    )


def canonicalize(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes.

    GCP schemas use integers and decimal strings, so the difficult binary-float
    portion of RFC 8785 is intentionally outside the accepted v0.1 domain.
    Object member ordering follows UTF-16 code units as required by JCS.
    """

    _validate(value)

    def encode(item: Any) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if isinstance(item, int):
            return str(item)
        if isinstance(item, str):
            return json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if isinstance(item, list):
            return "[" + ",".join(encode(element) for element in item) + "]"
        keys = sorted(item, key=_utf16_sort_key)
        return "{" + ",".join(encode(key) + ":" + encode(item[key]) for key in keys) + "}"

    return encode(value).encode("utf-8")


def without_proof(artifact: Any) -> Any:
    """Return a shallow artifact copy with its embedded proof removed."""

    if not isinstance(artifact, dict):
        raise GCPError(ErrorCode.UNSUPPORTED_SEMANTICS, "A signed artifact must be an object")
    return {key: value for key, value in artifact.items() if key != "proof"}

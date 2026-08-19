# Microsoft ACS Integration

Status: adapter contract implemented; native-runtime execution pending Python 3.11 environment

Primary-source baseline: Microsoft Agent Governance Toolkit commit `7d0cef5d9820a865c3c19b07bd39ecf7053b58a1`, reviewed 2026-08-19.

## Boundary

Microsoft Agent Control Specification (ACS) is a stateless policy decision runtime. The host supplies a complete intervention-point snapshot, ACS returns a normalized verdict, and the host enforces it. This is complementary to the Governance Capsule architecture:

- ACS supplies deterministic local policy decisions.
- The GCP kernel verifies portable task-governance invariants and current authority.
- CARM considers conflicts among otherwise valid policies using graph consequences.
- The Governed Action Gateway owns durable state and the final commit boundary.

The adapter is intentionally optional and structurally typed. Importing `gcp_reference` does not import ACS or require its native wheel.

## Verdict mapping

| ACS verdict | Normalized effect | Preserved control |
|---|---|---|
| `allow` | `ALLOW` | none |
| `warn` | `ALLOW` | `ACS_WARNING_AUDIT` |
| `transform` | `ALLOW` | `ACS_APPLY_TRANSFORM` |
| `deny` | `BLOCK` | none |
| `escalate` | `REQUIRE_APPROVAL` | cannot be relaxed by CARM |

The adapter also preserves the native verdict, reason code, runtime identity, policy identity/version, and ACS evidence artefact. An unknown verdict or runtime exception fails closed with a deterministic GCP error. Exception text is not copied into error evidence.

`warn` and `transform` are not silently flattened into an unconditional allow. The action gateway must audit the former and apply the verified transformed target for the latter before committing an action.

## Supported Python surface

The adapter supports the synchronous ACS `HostSession.evaluate(point, **snapshot)` surface and the documented direct/test shape `evaluate(point, snapshot)`. It emits the published `pre_tool_call` snapshot fields:

```json
{
  "tool_call": {
    "id": "call-7",
    "name": "create_vendor",
    "args": {
      "resource": "vendor:42",
      "parameters_digest": "sha256:..."
    }
  },
  "metadata": {}
}
```

Applications can supply a custom snapshot builder when their ACS manifest expects richer actor, tenant, approval, transport, or governance-capsule context.

## Installation gate

The reviewed ACS Python SDK is version `0.3.1b1` and requires Python 3.11 or newer. The current local GCP workspace runs Python 3.9.6, so its native wheel has not been executed here. Contract tests use both mapping-shaped FFI output and object/enum-shaped SDK output derived from the published Microsoft source.

In a Python 3.11 environment:

```sh
python3.11 -m venv .venv311
. .venv311/bin/activate
python -m pip install -e '.[acs]'
python -m pytest
```

Passing the current tests establishes mapping compatibility, not end-to-end compatibility with the native ACS runtime. The next acceptance gate is a pinned live manifest exercising all five verdicts through `HostSession`, followed by comparison against CARM using identical policy evidence.

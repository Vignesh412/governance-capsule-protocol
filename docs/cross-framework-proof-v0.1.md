# Cross-framework governed delegation proof v0.1

## Claim

The reference implementation can export application-owned governance at an OpenAI Agents SDK handoff-shaped boundary, carry it in a signed framework-neutral envelope, verify it at a Google ADK tool-callback-shaped boundary, and compose the verified delegation into the Governed Action Gateway.

This is a deterministic **SDK-contract proof**. The optional OpenAI Agents SDK and Google ADK packages are not installed in the current test environment, so this milestone does not claim native model-driven execution.

## Route

```text
OpenAI RunContextWrapper.context
    -> OpenAI handoff adapter
    -> signed GCP cross-framework transport
    -> Google ADK receiving boundary
    -> delegated-capsule verifier
    -> Governed Action Gateway
    -> idempotent supplier connector
```

## Transport bindings

The transport signature covers:

- source framework and runtime identity;
- destination framework and runtime identity;
- exact action proposal;
- ordered parent/child capsules and delegation proofs;
- creation and expiration times;
- transport ID; and
- single-use nonce.

The receiving boundary verifies the transport signer role, destination, lifetime, replay state, and exact proposal before composing the existing lineage verifier.

The ADK before-tool adapter never returns `None` for a protected call. It returns the Governed Action Gateway result, which causes ADK to skip the original raw tool, or returns a fail-closed result when no governed executor is configured. This preserves the gateway as the sole supplier-connector caller.

## Demonstrated controls

Successful execution places these controls in the signed gateway receipt:

- `GCP_CROSS_FRAMEWORK_TRANSPORT_VERIFIED`
- `GCP_SOURCE_OPENAI_HANDOFF_VERIFIED`
- `GCP_DESTINATION_GOOGLE_ADK_BOUNDARY_VERIFIED`
- `GCP_DELEGATION_LINEAGE_VERIFIED`

## Negative paths

The deterministic suite proves:

- post-signature transport mutation is rejected;
- transport nonce replay is rejected;
- child authority expansion is rejected before connector access; and
- cascading root revocation is rejected before connector access.

## Run

```sh
python3 tools/run_cross_framework_demo.py
python3 -m pytest -q tests/test_cross_framework_transport.py
```

The visual demo exposes the same real path as its first guided scenario.

## Next native gate

Install the optional SDKs in a Python 3.11 environment, instantiate their actual callback context/tool surfaces, and run pinned native contract tests without changing the GCP transport semantics. Live model routing is a subsequent evaluation concern and must not be conflated with deterministic authorization correctness.

```sh
uv venv --python 3.11
uv pip install -e '.[test,frameworks]'
uv run pytest -m frameworks_native tests/integration/test_cross_framework_native.py
```

The native test is present and skipped when the optional SDKs are absent. The restricted development sandbox could not download PyPI dependencies; this is an environment limitation, not a passing native result.

# Interactive Governance Capsule demo

This local web application presents nine deterministic governed-action scenarios and two optional live-native scenarios. The deterministic cross-framework proof carries a signed task from an OpenAI Agents SDK-shaped boundary to a Google ADK-shaped boundary. It also demonstrates a valid delegation that GCP verifies but CARM pauses because trusted runtime evidence creates a regulatory policy conflict. Live Native Mode runs both actual model SDKs when its dependencies and credentials are available: one action is allowed exactly once, while a revoked action is blocked with zero side effects.

## Start

### macOS — one click

Double-click **Open GCP Demo.command** in the repository folder. It prefers the isolated `.venv` Python when present, starts the governance kernel, opens the browser automatically, and immediately executes the strongest available scenario.

Keep the Terminal window opened by the launcher running while using the demo. Press Control-C in that window to stop it.

### Terminal

From the repository root:

```sh
python3 demo/server.py
```

Your browser should open [http://127.0.0.1:8765](http://127.0.0.1:8765). If it does not, open that address manually. The valid-delegation scenario executes as soon as the page loads. Selecting another scenario executes it immediately; **Run again** repeats the selected scenario. The interface pauses on the business context, then replays each verified boundary slowly enough to read and stops at the exact failed check before showing the final evidence.

Use a different port when 8765 is occupied:

```sh
python3 demo/server.py --port 9000
```

## What the demo proves

- A valid signed delegation with narrowed authority reaches the connector once.
- A signed OpenAI-to-Google-ADK transport is verified before the receiving tool boundary.
- Authority expansion, obligation removal, budget overallocation, and proof tampering are rejected before connector access.
- Revoking the root capsule stops its delegated descendant.
- A fully valid capsule can pass GCP while CARM separately escalates an unresolved sanctions-screening risk for human approval.
- Restart recovery reconciles a committed action without calling the idempotent connector twice.

The interface displays the returned gateway state, decision reason, connector-call count, capsule inheritance, verification trace, and signed enforcement receipt.

The browser is presentation only. Deterministic outcomes are produced in `demo/scenarios.py` by the same reference kernel exercised by the test suite. Live orchestration is implemented in `demo/native_showcase.py`; `/api/native/run` streams newline-delimited runtime events while execution is happening.

The risk scenario does not claim that CARM independently discovers truth or judges arbitrary plans. It consumes a trusted screening result, normalizes the resulting policy conflict, and enforces the configured approval boundary. GCP proves contract integrity; CARM evaluates current policy evidence.

## Live Native Mode

```sh
uv sync --python 3.11 --extra frameworks --extra test
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
.venv/bin/python demo/server.py
```

The live path proves a narrower, honest claim: real OpenAI and Google agent runtimes participate in one governed task, while signed application state—not model prose—remains the source of authority. If configuration is missing, the UI shows exactly what is required and defaults to the deterministic cross-framework proof.

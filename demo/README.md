# Interactive Governance Capsule demo

This local web application runs eight governed-action scenarios against the real Python reference implementation. The lead scenario carries a signed task from an OpenAI Agents SDK-shaped boundary to a Google ADK-shaped boundary.

## Start

### macOS — one click

Double-click **Open GCP Demo.command** in the repository folder. It starts the Python governance kernel, opens the browser automatically, and immediately executes the first scenario.

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
- Restart recovery reconciles a committed action without calling the idempotent connector twice.

The interface displays the returned gateway state, decision reason, connector-call count, capsule inheritance, verification trace, and signed enforcement receipt.

The browser is presentation only. Scenario outcomes are produced in `demo/scenarios.py` by the same reference kernel exercised by the test suite.

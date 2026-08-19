#!/usr/bin/env python3
"""Serve the GCP interactive demonstration without third-party web dependencies."""

import argparse
import json
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from demo.scenarios import run_scenario, scenario_catalog  # noqa: E402


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def log_message(self, format, *args):
        print("[gcp-demo] " + format % args)

    def _json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == "/api/scenarios":
            self._json(200, {"scenarios": scenario_catalog()})
            return
        super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/run":
            self._json(404, {"error": "Not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size) or b"{}")
            self._json(200, run_scenario(payload.get("scenario_id", "")))
        except (ValueError, json.JSONDecodeError) as error:
            self._json(400, {"error": str(error)})
        except Exception:
            self._json(500, {"error": "Scenario execution failed"})


def main():
    parser = argparse.ArgumentParser(description="Run the Governance Capsule visual demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DemoHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"Governance Capsule demo: {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDemo stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

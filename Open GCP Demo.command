#!/bin/zsh

set -e

DEMO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$DEMO_ROOT"

clear
echo "Starting Governance Capsule interactive demo..."
echo "The browser will open automatically."
echo "Keep this window open while using the demo."
echo

exec /usr/bin/env python3 demo/server.py

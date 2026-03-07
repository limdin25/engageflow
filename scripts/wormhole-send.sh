#!/usr/bin/env bash
# Run on server: zip engageflow workspace, then send via magic-wormhole (E2E encrypted).
# Receiver runs: wormhole receive <CODE>
set -e
WORKSPACE="${1:-/root/.openclaw/workspace-margarita/engageflow}"
echo "Zipping $WORKSPACE ..."
cd "$WORKSPACE"
zip -r /tmp/engageflow.zip .
echo "Installing magic-wormhole if needed ..."
pip install -q magic-wormhole 2>/dev/null || true
echo "Sending (give the code to the receiver):"
wormhole send /tmp/engageflow.zip

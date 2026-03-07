#!/usr/bin/env bash
# Run on server: zip engageflow workspace, then send via croc (E2E encrypted).
# Receiver runs: croc <CODE>
set -e
WORKSPACE="${1:-/root/.openclaw/workspace-margarita/engageflow}"
echo "Zipping $WORKSPACE ..."
cd "$WORKSPACE"
zip -r /tmp/engageflow.zip .
echo "Installing croc if needed ..."
command -v croc >/dev/null 2>&1 || curl -s https://getcroc.schollz.com | bash
echo "Sending (give the code to the receiver):"
croc send /tmp/engageflow.zip

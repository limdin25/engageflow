#!/usr/bin/env bash
# Run on server (e.g. Contabo): zip engageflow workspace and upload to transfer.sh
set -e
cd /root/.openclaw/workspace-margarita/engageflow/
zip -r /tmp/engageflow.zip .
curl --upload-file /tmp/engageflow.zip https://transfer.sh/engageflow.zip

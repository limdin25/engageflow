#!/bin/bash
# Railway access for Cursor. Run: ./scripts/railway-info.sh
# One-time: railway login (then railway link in repo)
set -e
cd "$(dirname "$0")/.."

echo "=== Railway status ==="
railway status 2>&1 || echo "(run: railway login && railway link --project \$RAILWAY_PROJECT_ID --service engageflow --environment DEV)"

echo ""
echo "=== Last 30 log lines ==="
railway logs --service engageflow 2>&1 | head -30 2>&1 || echo "(railway login required)"

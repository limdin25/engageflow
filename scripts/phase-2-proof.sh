#!/usr/bin/env bash
# Phase 2 proof: EngageFlow dbinfo, Joiner sync-cookies, Joiner profiles (no cookie content).
# Usage:
#   ./scripts/phase-2-proof.sh [ENGAGEFLOW_NEW_URL] [JOINER_NEW_URL]
#   For sync-cookies, set ENGAGEFLOW_JOINER_SECRET in env (not printed).
set -euo pipefail

ENGAGEFLOW_NEW_URL="${1:-https://engageflow-dev-ec26.up.railway.app}"
JOINER_NEW_URL="${2:-https://joiner-dev.up.railway.app}"

echo "=== 1) EngageFlow /debug/dbinfo ==="
curl -sS "$ENGAGEFLOW_NEW_URL/debug/dbinfo" | jq .
echo ""

echo "=== 2) Joiner sync-cookies (if ENGAGEFLOW_JOINER_SECRET set) ==="
if [ -n "${ENGAGEFLOW_JOINER_SECRET:-}" ]; then
  curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
    "$JOINER_NEW_URL/internal/joiner/sync-cookies" | jq .
else
  echo "(Skip: ENGAGEFLOW_JOINER_SECRET not set)"
fi
echo ""

echo "=== 3) Joiner /api/profiles (email, has_cookie_json, auth_status only) ==="
curl -sS "$JOINER_NEW_URL/api/profiles" | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json != null)), auth_status}'

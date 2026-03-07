#!/usr/bin/env bash
# Phase 2 restore: trigger restore with presigned URL, poll dbinfo, sync, profiles.
# Security: does not echo RESTORE_URL or ENGAGEFLOW_JOINER_SECRET.
#
# Prereqs (set in env, do not paste in chat):
#   export RESTORE_URL='<presigned-https-url>'
#   export ENGAGEFLOW_JOINER_SECRET='<railway-joiner-secret>'
#
# Usage: ./scripts/phase-2-restore-secure.sh
set -euo pipefail

ENGAGEFLOW_URL="${ENGAGEFLOW_URL:-https://engageflow-dev-ec26.up.railway.app}"
JOINER_URL="${JOINER_URL:-https://joiner-dev-abdb.up.railway.app}"

if [ -z "${RESTORE_URL:-}" ]; then
  echo "Error: RESTORE_URL is not set. Set it to a presigned HTTPS URL (do not paste in chat)." >&2
  exit 1
fi
if [ -z "${ENGAGEFLOW_JOINER_SECRET:-}" ]; then
  echo "Error: ENGAGEFLOW_JOINER_SECRET is not set." >&2
  exit 1
fi

echo "=== 1) Restore (expect 202) ==="
RESTORE_RESP=$(curl -sS -X POST \
  -H "Content-Type: application/json" \
  -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  -d "{\"url\":\"$RESTORE_URL\"}" \
  "$ENGAGEFLOW_URL/internal/restore-db")
echo "$RESTORE_RESP" | jq .
echo ""

echo "=== 2) Poll dbinfo until profiles_count > 0 (max 3 min) ==="
MAX_POLLS=36
POLL_INTERVAL=5
for i in $(seq 1 "$MAX_POLLS"); do
  INFO=$(curl -sS "$ENGAGEFLOW_URL/debug/dbinfo")
  COUNT=$(echo "$INFO" | jq -r '.profiles_count // 0')
  SIZE=$(echo "$INFO" | jq -r '.file_size_bytes // 0')
  if [ "$COUNT" != "0" ] && [ "$COUNT" != "null" ] && [ "${SIZE:-0}" -gt 139264 ] 2>/dev/null; then
    echo "Restored: profiles_count=$COUNT, file_size_bytes=$SIZE"
    break
  fi
  [ "$i" -eq "$MAX_POLLS" ] && { echo "Timeout waiting for restore."; exit 1; }
  sleep "$POLL_INTERVAL"
done
echo ""

echo "=== 3) dbinfo (after restore) ==="
curl -sS "$ENGAGEFLOW_URL/debug/dbinfo" | jq .
echo ""

echo "=== 4) Joiner sync-cookies ==="
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  "$JOINER_URL/internal/joiner/sync-cookies" | jq .
echo ""

echo "=== 5) Joiner profiles ==="
curl -sS "$JOINER_URL/api/profiles" | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'

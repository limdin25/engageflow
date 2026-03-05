#!/usr/bin/env bash
# Phase 0-1 proof: curl health/identity for engageflow-new, frontend-new, joiner-new.
# Usage: ./scripts/phase-0-1-proof.sh <engageflow-new-url> <frontend-new-url> <joiner-new-url>
# Example: ./scripts/phase-0-1-proof.sh https://engageflow-new.up.railway.app https://frontend-new.up.railway.app https://joiner-new.up.railway.app

set -e
EF="${1:?pass engageflow-new URL}"
FE="${2:?pass frontend-new URL}"
JO="${3:?pass joiner-new URL}"

echo "=== 1) EngageFlow (engageflow-new) ==="
curl -sS -i "$EF/health" | head -20
echo ""
echo "=== 2) Frontend (frontend-new) ==="
curl -sS -o /dev/null -w "HTTP %{http_code}\n" "$FE/"
echo ""
echo "=== 3) Joiner (joiner-new) ==="
curl -sS -i "$JO/" | head -20

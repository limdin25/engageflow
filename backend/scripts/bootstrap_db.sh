#!/usr/bin/env bash
set -e
DATA_DIR="${DATA_DIR:-/data}"
SEED_DB="$(dirname "$0")/../seed/engageflow.db"
TARGET_DB="${DATA_DIR}/engageflow.db"

mkdir -p "$DATA_DIR"
if [ ! -f "$TARGET_DB" ]; then
  if [ -f "$SEED_DB" ]; then
    cp "$SEED_DB" "$TARGET_DB"
    echo "Bootstrap: seeded $TARGET_DB from $SEED_DB"
  else
    echo "Bootstrap: no seed DB at $SEED_DB, using empty $TARGET_DB"
    touch "$TARGET_DB"
  fi
else
  echo "Bootstrap: $TARGET_DB exists, skipping seed"
fi

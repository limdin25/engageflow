#!/bin/bash
# VPS Setup: legacy branch + main/dev deployments
# Run this ON THE VPS after: ssh ubuntu@54.38.215.57
# Prereqs: git, docker, docker compose

set -e

GITHUB_REPO="https://github.com/limdin25/engageflow.git"
FIX_BRANCH="fix/profile-rotation-auth-timing-activity-feed"
MAIN_DIR="/var/www/engageflow"
DEV_DIR="/var/www/engageflow-dev"

echo "=== Step 0: Discover current setup ==="
if [ -d /var/www ]; then
  ls -la /var/www/
  CURRENT=$(find /var/www -name "docker-compose.yml" -o -name "app.py" 2>/dev/null | head -5)
  echo "Found: $CURRENT"
fi

# Find engageflow root (has backend/app.py or docker-compose.yml)
SEARCH_DIRS="/var/www /home/ubuntu /opt"
ROOT=""
for d in $SEARCH_DIRS; do
  [ ! -d "$d" ] && continue
  for sub in "$d"/*/; do
    [ -f "${sub}docker-compose.yml" ] || [ -f "${sub}backend/app.py" ] && { ROOT="${sub%/}"; break 2; }
  done
done

if [ -z "$ROOT" ]; then
  echo "ERROR: Could not find EngageFlow. Create /var/www/engageflow and clone first?"
  echo "  mkdir -p /var/www && cd /var/www && git clone $GITHUB_REPO engageflow"
  exit 1
fi

echo "EngageFlow root: $ROOT"
cd "$ROOT"

echo ""
echo "=== Step 1: Ensure git repo ==="
if [ ! -d .git ]; then
  git init
  git remote add origin "$GITHUB_REPO"
  git fetch origin
  git add -A
  git commit -m "Legacy: pre-setup snapshot" || true
  LEGACY_FROM="HEAD"
else
  git status
  if [ -n "$(git status -s)" ]; then
    git add -A
    git commit -m "Legacy: uncommitted changes before setup" || true
  fi
  LEGACY_FROM="HEAD"
fi

echo ""
echo "=== Step 2: Create legacy branch ==="
git branch -D legacy 2>/dev/null || true
git branch legacy "$LEGACY_FROM"
echo "Created branch: legacy"

echo ""
echo "=== Step 3: Add GitHub remote and fetch ==="
git remote remove origin 2>/dev/null || true
git remote add origin "$GITHUB_REPO"
git fetch origin

echo ""
echo "=== Step 4: Create main and dev from fix branch ==="
git branch -D main 2>/dev/null || true
git branch -D dev 2>/dev/null || true
git checkout -b main "origin/$FIX_BRANCH"
git checkout -b dev "origin/$FIX_BRANCH"
echo "Created main and dev from $FIX_BRANCH"

echo ""
echo "=== Step 5: Set up main deployment ($MAIN_DIR) ==="
sudo mkdir -p "$MAIN_DIR"
sudo chown -R "$(whoami):$(whoami)" "$MAIN_DIR" 2>/dev/null || true
git checkout main
rsync -a --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='*.db' --exclude='skool_accounts' --exclude='skool_*.json' ./ "$MAIN_DIR/"
if [ -f "$ROOT/backend/.env" ]; then
  cp "$ROOT/backend/.env" "$MAIN_DIR/backend/.env" 2>/dev/null || true
fi
echo "Main deployment: $MAIN_DIR"

echo ""
echo "=== Step 6: Set up dev deployment ($DEV_DIR) ==="
sudo mkdir -p "$DEV_DIR"
sudo chown -R "$(whoami):$(whoami)" "$DEV_DIR" 2>/dev/null || true
git checkout dev
rsync -a --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='*.db' --exclude='skool_accounts' --exclude='skool_*.json' ./ "$DEV_DIR/"
if [ -f "$ROOT/backend/.env" ]; then
  cp "$ROOT/backend/.env" "$DEV_DIR/backend/.env" 2>/dev/null || true
fi
echo "Dev deployment: $DEV_DIR"

git checkout main 2>/dev/null || true

echo ""
echo "=== Done ==="
echo "Legacy: branch only (current code preserved)"
echo "Main:   $MAIN_DIR  (checkout main)"
echo "Dev:    $DEV_DIR   (checkout dev)"
echo ""
echo "Next: Configure docker/nginx for ports (main=80, dev=3001)"
echo "  cd $MAIN_DIR && docker compose up -d"
echo "  cd $DEV_DIR && (edit docker-compose ports) && docker compose up -d"

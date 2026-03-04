# PROJECT STATE — Hot Takeover

Max 300 lines. Current truth only.

**Docs:** DISCIPLINE.md | PROJECT_STATE.md | PROJECT_HISTORY.md | RAILWAY_ACCESS.md | SECRETS_SETUP.md

## Current Objective

Automation platform for engagement workflows: backend API + automation engine, frontend dashboard.

## GitHub

- Repo: https://github.com/limdin25/engageflow
- Default branch: dev  ← active engineering branch (GitHub repo default = main)
- PR #1 (audit fixes): fix/profile-rotation-auth-timing-activity-feed

## Railway (project: efficient-ambition)

| Env | Frontend | Backend (service: engageflow) |
|-----|----------|-------------------------------|
| DEV | https://selfless-renewal-dev.up.railway.app | https://engageflow-dev.up.railway.app |
| PROD | https://selfless-renewal-production-9e39.up.railway.app | (same project, production env) |

Project ID: `f2cddd1a-3d44-47f6-bd18-5ce566b88da4`. Services: `engageflow` (backend), `selfless-renewal` (frontend), **joiner** (Node, monorepo subpath).

## System Status

Working / Partial / Broken

- Backend (FastAPI): Working
- Frontend (React/Vite): Working
- Automation engine: Working
- Docker compose: Working

## Architecture Snapshot

```
[Frontend :80] → nginx → /api/* → [Backend :8000]
                      ↘ serves UI
```

Backend: FastAPI, SQLite (engageflow.db), automation engine. Automation control routes accept BOTH /automation/* and /api/automation/* (UI may call either).
Frontend: React, Vite, React Query, TanStack Router.

**Request correlation:** Every request gets a short `request_id` (8-char UUID prefix). Response headers: `X-Request-Id`, `X-EngageFlow-Git-Sha`. Automation control JSON includes `request_id`. On error, frontend toast shows `(request_id: xxx)` so Railway logs can be traced in &lt;1 min.

**Stop never 500:** POST /api/automation/stop always returns 200. Response: `{ ok, success, isRunning, status, error?, request_id }`. On engine failure (CancelledError, Exception), returns 200 with `ok: false` and `error`. Stop failures appended to in-memory `recent_errors` (exposed in /api/diagnostics).

**Stop persists:** Stop sets `masterEnabled=false` in automation_settings. Start sets `masterEnabled=true`. On startup, if `masterEnabled=false` in DB, auto-start is skipped (log: "Auto-start suppressed by DB flag"). Prevents "I clicked Stop and it kept running" after container restarts.

**Diagnostics/Start:** db_master_enabled always boolean (never null). POST /api/automation/start accepts no body or {}. Stop has 8s timeout to avoid 502.

**Skool editor:** 3s post-load delay + 25s timeout, 5 selector variants, page-state diagnostics on editor_not_visible.

## How To Run

**Docker (recommended):**
```sh
docker compose up --build -d
```
UI: http://localhost | API: http://localhost/api/...

**Local dev:**
```sh
cd backend && pip install -r requirements.txt && uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
```sh
cd frontend && npm i && npm run dev
```

## Healthy System Definition

The system is considered healthy when:

- No duplicate events or state entries occur.
- Each step transitions start → complete exactly once.
- No step remains running beyond timeout.
- Preview or output artifacts are generated when expected.
- No background process runs indefinitely.
- /health returns OK when applicable.

## Known Risks

1. Skool.com API changes may break automation.
2. Browser/session state can become stale; profiles require periodic re-auth.
3. SQLite lock under concurrent writes; backend has retry logic and log buffer.

## DEV Deployment (2026-03-04)

**Canonical DEV = Railway.** UI and automation run on Railway; VPS is legacy (automation disabled after Railway proves healthy).

- **Branch:** dev (MANDATORY; do NOT touch main)
- **Frontend DEV:** https://selfless-renewal-dev.up.railway.app
- **Backend DEV (Railway):** https://engageflow-dev.up.railway.app
- **DEV VPS (legacy):** 72.61.147.80, path /docker/engageflow-dev, port 3001 — DO NOT DELETE YET; disable automation only after Railway passes.

### Railway DEV Variables (engageflow service)

| Variable | Value | Required |
|----------|-------|----------|
| ENGAGEFLOW_DB_PATH | /data/engageflow.db | Yes |
| ENGAGEFLOW_AUTOMATION_ENABLED | 1 | Yes |
| ENGAGEFLOW_DEBUG | 1 | Temporary (proof) |
| OPENAI_API_KEY | sk-... | Yes |

Backend MUST have a Volume mounted at `/data`. Redeploy after variable changes.

### Joiner service (DEV)

- **URL:** https://joiner-dev.up.railway.app
- **Source:** Repo `limdin25/engageflow`, branch `dev`, **Root Directory:** `joiner/backend`, Dockerfile `joiner/backend/Dockerfile`.
- **DB source of truth:** EngageFlow DB (`ENGAGEFLOW_DB_PATH`). Local: `backend/engageflow.db` (same file as EngageFlow backend). Railway: `/data/engageflow.db`. Joiner ensures `profiles.cookie_json` on startup (migration adds column if missing); fails fast if required column missing.
- **DB debug:** `GET /internal/joiner/debug/db-info` with header `X-JOINER-SECRET`. Returns `db_kind`, `db_path` (basename), `schema_hash`, `profiles_has_cookie_json`. No secrets.
- **Startup log:** `[db] engageflow db_kind=sqlite db_path=<basename> schema_hash=<hash>`.
- **Deployment fingerprint:** Response header `X-Joiner-Git-Sha` (commit hash or `unknown`); set from `RAILWAY_GIT_COMMIT_SHA` / `ENGAGEFLOW_GIT_SHA`.
- **Cookie sync:** `POST /internal/joiner/sync-cookies` with header `X-JOINER-SECRET: <ENGAGEFLOW_JOINER_SECRET>`. Returns `{ success, scanned, updated }`. Validated 2026-03-04 (200, scanned:3, updated:0).

| Variable | Value | Required |
|----------|-------|----------|
| ENGAGEFLOW_JOINER_SECRET | Secure random (dev: set in Railway; rotate for prod) | Yes |

### Railway DEV Variables (selfless-renewal service)

| Variable | Value | Required |
|----------|-------|----------|
| VITE_BACKEND_URL | https://engageflow-dev.up.railway.app | Yes |

Without this, deployed frontend throws "VITE_BACKEND_URL must be set when deployed".

### Verification curls (Railway DEV)

Cursor runs these (do not ask user):

```sh
curl -sS https://engageflow-dev.up.railway.app/health
# PASS: {"status":"ok","running":true}

curl -sS https://engageflow-dev.up.railway.app/api/db-status
# PASS: db_path=/data/engageflow.db, writable=true, db_file_exists=true

curl -sS https://engageflow-dev.up.railway.app/debug/runtime
# PASS: db_path=/data/engageflow.db, engine_running=true (requires ENGAGEFLOW_DEBUG=1)

curl -sS "https://engageflow-dev.up.railway.app/activity?limit=1"
# PASS: newest timestamp < 5 min when actions execute

curl -i -X POST https://engageflow-dev.up.railway.app/automation/stop
# PASS: 200, JSON with isRunning=false, request_id; header X-Request-Id present (idempotent when already stopped)

curl -sS https://engageflow-dev.up.railway.app/api/diagnostics
# PASS: JSON with git_sha, build_time_utc, service_name, system_health, database_status, automation_engine_state, last_activity_timestamp, recent_errors, environment_flags, scheduler_truth_packet (now_server_utc, next_action_id, next_run_at_absolute, eta_seconds, scheduler_source_of_truth, db_path, engine_state)
# Response header X-EngageFlow-Git-Sha matches deployed commit
```

### Railway build config (2026-03-04)

- **Root Dockerfile:** `Dockerfile` at repo root builds backend from `backend/` (monorepo). Uses `railway.json` to point to it.
- **PORT:** Backend CMD uses `$PORT` (Railway sets it; default 8000 local). Fixes 502/port mismatch.
- **engageflow service:** If Railway uses root = backend, `backend/Dockerfile` is used. If root = `.`, root `Dockerfile` + `railway.json` used.

### VPS disable (only after Railway passes)

On VPS: set `ENGAGEFLOW_AUTOMATION_ENABLED=0` in docker-compose, then `docker compose up -d --build`. Verify: `curl -sS http://72.61.147.80:3001/api/health` → `running:false`.

## Dashboard Scheduling UI (2026-03-03)

**Status:** Auto-refresh + guarantee signal deployed to dev.

- **Action Queue:** Up to 30 upcoming actions (queue=30, not capped at 2/6). "Updated: Xs ago" shown.
- **Profile interleaving (Robinhood rule):** No two consecutive items from same profile when multiple profiles have actions; single-profile repeats allowed.
- **Activity Timeline:** Newest first (ORDER BY timestamp DESC); last comment/action at top. **Display:** dedupe by id (or profile+groupName+action+timestamp), interleave by profile (round-robin), slice 30. UI-only; no backend changes. Auto-refresh every 10s; refetch on window focus. "Last updated: Xs ago". "No new activity detected in last N min" when newest &gt; 10 min old.
- **Countdown:** Always visible; ticks every second ("Next action in 14m 22s"); "No actions scheduled" when empty.

### H) DEV UI verification (Hugo)

**URL:** https://selfless-renewal-dev.up.railway.app — Dashboard page.

1. **Action Queue:** Up to 30 items; not capped at 2/6.
2. **Profile interleaving:** No consecutive same profile when multiple profiles exist.
3. **Activity Timeline:** Newest activity first; last comment/action at top after refresh.
4. **Countdown:** Visible; ticks every second or "No actions scheduled" when empty.

**Reply:** "verified" OR "broken: &lt;what is wrong&gt;"

### I) Rollback readiness

**Trigger rollback immediately if ANY occur:**
- Tests fail
- Health check fails: `curl -sf http://72.61.147.80:3001/api/health`
- Scheduler not running
- DB constraint errors
- Backend logs contain errors/exceptions within 2 min: `docker logs engageflow-dev-backend --since 2m | grep -i "error|exception"`

**Rollback steps (MANDATORY):**
1. `git revert HEAD --no-edit`
2. `git push origin dev`
3. On Dev VPS: `cd /docker/engageflow-dev` → `git pull origin dev` → `docker compose up -d --build`

## Recent Fixes (2026-03-03)

1. Profile rotation: profile_last_attempt updated at top of sync loop (no stuck single account).
2. Auth marker timing: wait_for_selector replaces blind sleep in app.py and engine.py.
3. Activity feed: canonical profiles.name used for activity_feed.profile (no name mismatch).
4. Log buffering: locked-DB log writes buffered and flushed after sync cycle.
5. **8 surgical audit fixes (dev branch):** (1) deadlock prevention in finally block, (2) log buffer ts key, (3) Buffered not Skipped message, (4) profile_for_feed UUID→SYSTEM fallback, (6) backfill profile resolution from DB, (7) docker-compose.dev volume for live reload, (8) requeue prepend for log order.

## Recent Fixes (2026-03-03 cont.)

6. **Queue/activity dashboard fixes [TD-124]:** read_queue limit=30, read_activity limit=100, engine UTC timestamps. TDD tests in backend/tests/.

## Railway DEV Automation (2026-03-04)

- **Problem:** `curl https://engageflow-dev.up.railway.app/health` returned `running:false` — scheduler not started.
- **Fix:** `ENGAGEFLOW_AUTOMATION_ENABLED=1` (default OFF) auto-starts scheduler in lifespan when DB writable.
- **DB path:** `ENGAGEFLOW_DB_PATH=/data/engageflow.db` (Railway volume). If not set, backend uses repo default.
- **TDD:** backend/tests/test_health_automation.py — test_health_running_false_when_disabled, test_health_running_true_when_scheduler_started, test_activity_updates_when_action_executes.

## Activity Timeline "19 hr ago" Root Cause (2026-03-04) — PROVED

- **Symptom:** UI shows "19 hr ago" even when automation comments now; queue/countdown show upcoming actions.
- **Root cause (H1 ENV/DB mismatch):** Railway DEV and Dev VPS return different activity data (different IDs). Railway reads `/data/engageflow.db`; VPS reads `/root/engageflow-shared/engageflow.db`. Automation runs on one env, UI reads from another.
- **Canonical DEV pairing (no ambiguity):**
  - **Option A (preferred):** Railway DEV UI + Railway DEV backend. Set `ENGAGEFLOW_AUTOMATION_ENABLED=1`, `ENGAGEFLOW_DB_PATH=/data/engageflow.db`, OpenAI key. Engine runs in Railway, writes to same DB.
  - **Option B:** Dev VPS UI + Dev VPS backend. Frontend at http://72.61.147.80:3001 uses /api proxy to same-host backend. Engine runs on VPS, writes to `/root/engageflow-shared/engageflow.db`.
- **Proof signal:** `GET /debug/runtime` (requires `ENGAGEFLOW_DEBUG=1`) returns db_path, db_file_exists, engine_running, newest_activity_timestamp, newest_queue_scheduledFor. Use to verify no guessing.
- **Defensive:** Backend normalizes activity timestamps (append Z when no timezone). backend/tests/test_activity_timestamp.py, test_debug_runtime.py.

## Railway Autonomy (2026-03-04)

**Level:** Cursor → GitHub Actions → Railway CLI. No browser for vars/logs/deploy.

| Component | Status | Access |
|-----------|--------|--------|
| GitHub Secrets | ✅ | RAILWAY_TOKEN, RAILWAY_TOKEN_PROD, RAILWAY_PROJECT_ID |
| Workflow | 🔄 | Fixed: railway link --project, railway variable set. Re-run on push. |
| Railway backend | ❌ 502 | engageflow-dev not responding |
| /debug/logs | — | Unreachable while backend 502 |

**What Cursor controls:**
- Push to dev → workflow sets ENGAGEFLOW_DEBUG=1 via Railway CLI
- Push to main → workflow sets ENGAGEFLOW_DEBUG=0 via Railway CLI
- `/debug/logs` → last 100 lines (when backend up + ENGAGEFLOW_DEBUG=1)
- `railway logs --service engageflow` (local, after `railway login`)

**Workflow:** `.github/workflows/railway.yml`. **Secrets:** See `docs/SECRETS_SETUP.md`.

## Next Actions (max 10)

1. Add `RAILWAY_API_TOKEN` (account token) for workflow `railway link` step.
2. Set Railway DEV Variables on engageflow service: `ENGAGEFLOW_AUTOMATION_ENABLED=1`, `ENGAGEFLOW_DB_PATH=/data/engageflow.db`.
3. Verify profile rotation with 2+ profiles in production.
4. Verify activity timeline shows rows for all active profiles.
5. Entry #39: Countdown fix — julianday() for queue datetime comparison (string comparison excluded space format).
6. —
7. —
8. —
9. —
10. —

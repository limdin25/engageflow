# PROJECT STATE — Hot Takeover

Max 300 lines. Current truth only.

## Current Objective

Automation platform for engagement workflows: backend API + automation engine, frontend dashboard.

## GitHub

- Repo: https://github.com/limdin25/engageflow
- Default branch: main
- PR #1 (audit fixes): fix/profile-rotation-auth-timing-activity-feed

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

Backend: FastAPI, SQLite (engageflow.db), automation engine.
Frontend: React, Vite, React Query, TanStack Router.

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

## DEV Deployment (2026-03-03)

- **Branch:** dev (commit 8e58c34, 7ec6fb3)
- **Pushed:** Yes (force push; remote dev had diverged)
- **Frontend DEV:** https://selfless-renewal-dev.up.railway.app
- **DEV VPS:** 72.61.147.80, path /docker/engageflow-dev, port 3001
- **Deploy steps:** `ssh root@72.61.147.80` → `cd /docker/engageflow-dev` → `git pull origin dev` → `docker compose up -d --build`
- **Health:** `curl -sf http://72.61.147.80:3001/api/health`

## Dashboard Scheduling UI (2026-03-03)

**Status:** Deployed to dev. Awaiting Hugo verification.

- **Action Queue:** Up to 30 upcoming actions (queue=30, not capped at 2/6).
- **Profile interleaving (Robinhood rule):** No two consecutive items from same profile when multiple profiles have actions; single-profile repeats allowed.
- **Activity Timeline:** Newest first (ORDER BY timestamp DESC); last comment/action at top.
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

## Next Actions (max 10)

1. Verify profile rotation with 2+ profiles in production.
2. Verify activity timeline shows rows for all active profiles.
3. ~~Deploy queue/activity fixes to dev~~ Done. dev pushed (8e58c34). DEV VPS: manual deploy required (ssh root@72.61.147.80, cd /docker/engageflow-dev, git pull origin dev, docker compose up -d --build).
4. —
4. —
5. —
6. —
7. —
8. —
9. —
10. —

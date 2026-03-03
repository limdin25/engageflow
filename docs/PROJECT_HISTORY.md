# PROJECT HISTORY — EngageFlow + Joiner

Append-only log of significant changes.

---

## 2026-03-02 — Hybrid Integration Complete

**Phase 4–5: Frontend + PM2**

- **AccountsTab**: Patched for hybrid — removed Add Account and Delete Account buttons. Profiles read from EngageFlow via joiner API. Uses joiner-api and ./StatusBadge.
- **QueueTab, SurveyTab, LogsTab**: Switched to joiner-api (./joiner-api).
- **joiner-api.ts**: BASE set to `/api/joiner` for nginx proxy.
- **CommunitiesPage**: Join tab mock replaced with real 4-tab layout: Accounts, Survey Info, Communities & Queue, Live Logs.
- **nginx**: Added `location /api/joiner/` → proxy to joiner backend (3100). Rewrite strips `/api/joiner` prefix.
- **PM2**: Started `engageflow-joiner` from `engageflow/joiner/backend`.
- **Frontend**: Rebuilt successfully.

**Docs**: DISCIPLINE.md, PROJECT_STATE.md created in engageflow/docs/.

---

## 2026-03-03 — Railway Deployment (Contabo DB Preserved)

**Change:** Prepare for Railway with full SQLite DB from Contabo. No migration, no reset.

**Files:**
- backend/seed/engageflow.db — full DB (1.8MB) from Contabo
- backend/scripts/bootstrap_db.sh — copy seed to /data if not exists
- Procfile — bootstrap + uvicorn
- backend/app.py — ENGAGEFLOW_DB_PATH env, GET /api/db-status
- .gitignore — *.db-wal, *.db-shm; !backend/seed/engageflow.db

**Verification:** After deploy, GET /api/db-status shows DB path, size > 0, tables populated.

---

## 2026-03-03 — Fix Railway frontend Docker build

**Change:** Frontend Dockerfile failed because Railway uses repo root as build context when Dockerfile path is frontend/Dockerfile. COPY package*.json found no file at root.

**Files:**
- frontend/Dockerfile — COPY frontend/package*.json, COPY frontend/., COPY frontend/nginx.conf

**Evidence:** package.json has "build": "vite build"; Vite outputs to dist/ by default. nginx.conf has try_files $uri $uri/ /index.html for SPA.

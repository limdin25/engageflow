# PROJECT STATE — EngageFlow + Joiner Hybrid

**Last updated:** 2026-03-03
**Max 300 lines.**

---

## GitHub & Railway

- Repo: https://github.com/limdin25/engageflow
- Railway-ready: backend/seed/engageflow.db (Contabo DB preserved), bootstrap_db.sh, Procfile
- DB path: ENGAGEFLOW_DB_PATH (default /data/engageflow.db on Railway volume)
- Debug: GET /api/db-status (DB path, size, table counts)

**Frontend service (selfless-renewal):**
- Dockerfile path: frontend/Dockerfile (build context = repo root)
- Vite output: dist/ (Dockerfile copies /app/dist)
- **Required variable:** `VITE_BACKEND_URL=https://engageflow-production.up.railway.app` (frontend calls backend directly; nginx /api proxy does not resolve on Railway)

---

## Current Objective

Integrate community-join-manager into EngageFlow as `engageflow/joiner/`. Hybrid architecture: shared profiles + browser profiles, separate joiner DB, browser locks for coordination.

---

## System Status

| Component | Port | Status | Notes |
|-----------|------|--------|-------|
| EngageFlow backend | 3103 | Running | FastAPI, engageflow.db |
| EngageFlow frontend | 3080 | Served | Static from dist/, nginx |
| Joiner backend | 3100 | Running | Node/Express, joiner.db |

---

## Architecture

```
engageflow/
├── backend/          # FastAPI — engagement automation, engageflow.db
├── frontend/         # React — unified dashboard
├── joiner/           # Node.js — join automation
│   ├── backend/      # server.js, joiner.db, config.js
│   └── src/          # Components (copied to frontend)
└── engageflow.db     # profiles, communities, browser_locks
```

**Database access:**
| Table | DB | Joiner | EngageFlow |
|-------|-----|--------|------------|
| profiles | engageflow.db | READ | RW |
| browser_locks | engageflow.db | RW | RW |
| communities | engageflow.db | Webhook write | RW |
| join_queue | joiner.db | RW | — |
| profile_discovery_info | joiner.db | RW | — |

---

## Join Tab Structure

Communities page → Join tab → 4 sub-tabs:
- **Accounts** — Per-account stats, Run/Stop, Cancel Pending (AccountsTab)
- **Survey Info** — Discovery info per profile (SurveyTab)
- **Communities & Queue** — Add to queue, manage queue (QueueTab)
- **Live Logs** — Join logs (LogsTab)

---

## API Proxy

- `/api/` → EngageFlow backend (3103)
- `/api/joiner/` → Joiner backend (3100), rewrite to `/api/`

---

## Next Actions

1. ~~Wire Join tab with all 4 components.~~ Done.
2. ~~Add nginx location for /api/joiner/.~~ Done.
3. ~~PM2 start engageflow-joiner.~~ Done.
4. ~~Remove Add/Delete from AccountsTab.~~ Done.
5. Manual test: open http://38.242.229.161:3080/communities → Join tab → Accounts/Survey/Queue/Logs.

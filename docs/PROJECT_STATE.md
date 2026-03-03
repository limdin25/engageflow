# PROJECT STATE — Hot Takeover

Max 300 lines. Current truth only.

## Current Objective

Automation platform for engagement workflows: backend API + automation engine, frontend dashboard.

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
3. SQLite lock under concurrent writes; backend has retry logic.

## Next Actions (max 10)

1. —
2. —
3. —
4. —
5. —
6. —
7. —
8. —
9. —
10. —

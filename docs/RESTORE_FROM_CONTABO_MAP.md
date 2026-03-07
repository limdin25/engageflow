# Restore EngageFlow + Joiner from Contabo — map and checklist

**Source (single source of truth):** Contabo VPS `38.242.229.161`  
**SSH:** `ssh -i ~/.ssh/openclaw_tunnel root@38.242.229.161`  
**Path:** `/root/.openclaw/workspace-margarita/engageflow/`

---

## 1. What lives on Contabo

| Item | Path on Contabo | Notes |
|------|----------------------------------|--------|
| **Repo root** | `/root/.openclaw/workspace-margarita/engageflow/` | backend, frontend, joiner, docs, scripts |
| **Backend** | `.../backend/` | FastAPI app, `app.py`, requirements.txt |
| **Frontend** | `.../frontend/` | React/Vite app |
| **Joiner** | `.../joiner/` | Full app: joiner/backend (Node), joiner/src (UI), dist, etc. |
| **Real DB** | `.../backend/engageflow.db` | SQLite, ~2.7 MB — **real data** (profiles, communities, activity) |
| **Docker** | `.../docker-compose.yml` | backend + frontend; mounts `./backend:/app` |
| **Secrets** | `.../backend/.env` | Not to be committed; copy manually if needed |

Contabo has **no** `docker-compose.coolify.yml`; that was added for Coolify/Hostinger deploy and can be re-added after restore if you deploy there again.

---

## 2. Restore checklist (code → GitHub)

1. **Pull code from Contabo** (exclude .git, node_modules, .pytest_cache, *.tar.gz, __pycache__, .env, *.db)
2. **Export DB from Contabo** (for real data backup / restore elsewhere)
3. **Ensure .gitignore** excludes `.env`, `*.db`, `engageflow.db`, `node_modules`, `venv`, `.pytest_cache`, `*.tar.gz`.
4. **Commit and push** to GitHub (dev and main as needed).
5. **Re-add Coolify-specific files** if you deploy again on Coolify (e.g. `docker-compose.coolify.yml`, frontend `VITE_BACKEND_URL` build arg).

---

## 3. Where the real data is

- **On Contabo:** `/root/.openclaw/workspace-margarita/engageflow/backend/engageflow.db` (live SQLite).
- **After restore:** A copy can be kept as `engageflow-db-backup-from-contabo-YYYY-MM-DD.db`; do **not** commit it to GitHub. When you deploy (e.g. Coolify, Railway), restore this DB into the backend volume/path used by that deploy.

---

## 4. Joiner

Joiner is inside the same repo on Contabo: `engageflow/joiner/`. It includes:
- `joiner/backend/` — Node server (e.g. server.js, package.json)
- `joiner/src/` — frontend source
- `joiner/dist/` — built frontend (can be regenerated)

Pushing the repo from Contabo to GitHub includes Joiner; no separate repo needed unless you split it later.

---

## 5. Verification after push

- GitHub `limdin25/engageflow` has branches dev (and main) with backend, frontend, joiner, and docs.
- DB backup file exists locally (or in a known backup path) and is **not** in the repo.
- If you deploy from GitHub again (e.g. Coolify), use the backup DB to restore real data to the new deployment.

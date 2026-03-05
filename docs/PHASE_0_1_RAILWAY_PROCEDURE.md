# Phase 0–1: Lock target + fix deploy pipeline (no DB migration)

**Goal:** Ensure Railway can deploy the exact VPS code from GitHub `dev` with clean rollback.  
**Rules:** No DB/cookie transfer yet. No destructive deletes; archive/rename only.

**Cursor has full Railway access** via CLI (`railway login` + link) and GraphQL API (token in `~/.railway/config.json` or `RAILWAY_API_TOKEN`). Step A and Step C can be executed via API; see docs/RAILWAY_ACCESS.md and JOINER_SOURCE_FIX_PROOF.md.

---

## Step A — Railway rollback safety

Do this in the **Railway dashboard** (Project → Services).

1. **Rename existing services** (archive only; do NOT delete volumes):
   - `engageflow` → **`engageflow-old`**
   - `joiner` → **`joiner-old`**
   - `frontend` → **`frontend-old`**

2. **Create three new services** (same project):
   - **`engageflow-new`**
   - **`joiner-new`**
   - **`frontend-new`**

3. **Do NOT delete any volumes** attached to the old services.

### Phase 0-1 execution via API (done)

Using token from `~/.railway/config.json` → `.user.token` and GraphQL `https://backboard.railway.com/graphql/v2`:

- **Renamed** (serviceUpdate): engageflow → engageflow-old, joiner → joiner-old, selfless-renewal → frontend-old.
- **Created** (serviceCreate): engageflow-new (`8c9582fe-4425-4490-b086-611a00f169b7`), frontend-new (`75b06f1e-444f-4230-9efd-c1ec182caab1`), joiner-new (`1c794d89-da1b-4b89-9364-aab7976d9613`).
- **Set root** (serviceInstanceUpdate, DEV env): engageflow-new → `backend`, frontend-new → `frontend`, joiner-new → `joiner/backend`.
- **Redeploy** (serviceInstanceRedeploy): called for all three *-new* services (builds will run once repo is connected).

**Repo connection:** New services are created empty. Connecting to GitHub (limdin25/engageflow, branch dev) requires the **Railway dashboard**: for each of engageflow-new, frontend-new, joiner-new → **Settings → Source → Connect Repo** → select repo and branch **dev**. Root directory is already set via API. Then **copy env vars** from engageflow-old, frontend-old, joiner-old; do not attach volumes. **Redeploy** (or trigger again via API). After deploy, add a **public domain** per service if needed, then run the proof script with the three URLs.

**engageflow front (done via API):** `VITE_BACKEND_URL` set to `https://engageflow-dev-ec26.up.railway.app`. Nginx fix (no backend upstream) pushed to **dev**. **You must:** Settings → Source → **Branch connected to DEV** → change from `main` to **`dev`**, then Deploy. Build will then use dev (with nginx fix) and the variable above.

**Frontend must listen on Railway’s PORT:** Railway injects a dynamic `PORT` (e.g. 8080). The frontend Dockerfile uses `nginx.conf.template` and `envsubst` at runtime so nginx listens on `$PORT`. Without this, you get "Application failed to respond".

---

## Step B — GitHub mirror from VPS

**On the VPS** (SSH to VPS, then):

```bash
cd /docker/engageflow-dev   # or your repo root

# 1) Status must be clean or committed
git status

# 2) Ensure .gitignore blocks DB, logs, node_modules, venv, shared data
#    (see repo .gitignore; add engageflow-shared if needed)

# 3) Commit working VPS code state (only code/docs; no DB or secrets)
git add -A
git reset -- backend/engageflow.db backend/engageflow.db-wal backend/engageflow.db-shm backend/logs/ backend/skool_accounts/ backend/.env .env .env.* 2>/dev/null || true
git status   # confirm no DB/logs staged
git commit -m "chore: phase 0-1 VPS code state for Railway deploy from dev"

# 4) Push to origin dev
git push origin dev

# 5) Record commit SHA
git rev-parse HEAD
```

**If you use the local repo instead of VPS:** run the same flow from the repo root (commit only code + docs, push `dev`), then record `git rev-parse HEAD`.

---

## Step C — Railway source config (new services)

In Railway, for each **new** service set **Source** as below. Then **Redeploy** all three.

| Service           | Branch | Root directory   | Dockerfile path        |
|------------------|--------|-------------------|------------------------|
| **engageflow-new** | `dev`  | `backend`         | `backend/Dockerfile` or `Dockerfile` (relative to root) |
| **frontend-new**  | `dev`  | `frontend`        | `frontend/Dockerfile` or `Dockerfile` (relative to root) |
| **joiner-new**    | `dev`  | `joiner/backend`  | `joiner/backend/Dockerfile` or `Dockerfile` (relative to root) |

- **engageflow-new:** Source → Connect repo (if not already) → Branch: **dev** → Root Directory: **backend** → Dockerfile path: **Dockerfile** (so it uses `backend/Dockerfile`).
- **frontend-new:** Branch: **dev** → Root Directory: **frontend** → Dockerfile path: **Dockerfile**.
- **joiner-new:** Branch: **dev** → Root Directory: **joiner/backend** → Dockerfile path: **Dockerfile**.

Set **variables** on the new services (copy from old services): e.g. `ENGAGEFLOW_DB_PATH`, `OPENAI_API_KEY`, `ENGAGEFLOW_JOINER_SECRET`, `VITE_BACKEND_URL`, etc. Do **not** attach volumes to the new services yet (Phase 0–1 is deploy pipeline only; DB migration later).

Redeploy all three and wait for builds to finish.

---

## Proof required

1. **GitHub dev commit SHA**  
   After Step B: **`8a5cb5447ac3356c3f4cc5b91462ab5ff50f1c14`** (dev @ 8a5cb54). Latest dev: **3084e78** (includes proof script).

2. **Railway build logs**  
   For each new service, open latest deployment → Build logs. Confirm:
   - **engageflow-new:** build context shows `backend/`, Dockerfile from `backend/Dockerfile`.
   - **frontend-new:** build context shows `frontend/`, Dockerfile from `frontend/Dockerfile`.
   - **joiner-new:** build context shows `joiner/backend/`, Dockerfile from `joiner/backend/Dockerfile`.

3. **Health / identity curls**  
   After deploy, get the **new** service URLs from Railway (e.g. engageflow-new → Settings → Domains). Then run:

   ```bash
   ./scripts/phase-0-1-proof.sh "https://<engageflow-new-url>" "https://<frontend-new-url>" "https://<joiner-new-url>"
   ```

   Or manually:

   ```bash
   # EngageFlow backend (engageflow-new)
   curl -sS https://<engageflow-new-url>/health
   # Expect: {"status":"ok", ...} and response header X-EngageFlow-Git-Sha

   # Frontend (frontend-new) — may redirect or serve HTML
   curl -sS -o /dev/null -w "%{http_code}" https://<frontend-new-url>/
   # Expect: 200

   # Joiner (joiner-new)
   curl -sS https://<joiner-new-url>/
   # Expect: {"status":"ok","service":"joiner"} or similar; header X-Joiner-Git-Sha
   ```

4. **Stop condition**  
   Do **not** migrate DB or attach production volumes until the above proof passes.

---

## Checklist

- [ ] Step A: Renamed engageflow/joiner/frontend to *-old; created *-new (no volume delete).
- [ ] Step B: Repo clean/committed; pushed to `origin dev`; SHA recorded.
- [ ] Step C: engageflow-new, frontend-new, joiner-new use branch **dev** and correct root/Dockerfile; redeployed.
- [ ] Proof: Build logs show correct roots; curl health returns expected identity for each new service.

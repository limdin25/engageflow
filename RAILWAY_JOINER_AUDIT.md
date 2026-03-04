# Railway Joiner 404 — Source + Build Context + Route Audit

## PHASE 1 — SOURCE SETTINGS (Railway UI)

**Joiner service → Settings → Source.** Record exactly:

| Field | Required value | Notes |
|-------|----------------|-------|
| **Repo URL** | (your GitHub repo, e.g. limdin25/engageflow) | Same as EngageFlow |
| **Branch** | `dev` | main = 2a8b986 (no sync route) |
| **Root Directory** | `joiner/backend` | So build uses joiner/backend/Dockerfile and server.js |
| **Build method** | Dockerfile | joiner/backend/railway.json specifies Dockerfile |

If **Root Directory** is empty or repo root, Railway builds from repo root and may use the **root** Dockerfile (EngageFlow Python), not Joiner. Set **Root Directory** to `joiner/backend`.

---

## PHASE 2 — BUILD COMMIT PROOF

After deploy, response header proves which commit is running:

```bash
curl -sS -i https://joiner-dev.up.railway.app/ | grep -i x-joiner-git-sha
```

**Expected after correct deploy from dev:** `X-Joiner-Git-Sha: 27f95a7...` (or current dev SHA).  
**If missing or old SHA:** Build did not use dev or Root Directory is wrong.

---

## PHASE 3 — BUILD CONTEXT

**Repo layout:**
- `joiner/backend/server.js` — Express app, registers `POST /internal/joiner/sync-cookies` (line 178)
- `joiner/backend/Dockerfile` — `WORKDIR /app`, `COPY . .`, `CMD ["node", "server.js"]`
- `joiner/backend/railway.json` — `dockerfilePath: "Dockerfile"`

**Railway must:**
- Use **Root Directory** = `joiner/backend` so that `COPY . .` is joiner/backend and `server.js` is present, **or**
- Use **Dockerfile path** = `joiner/backend/Dockerfile` with build context = `joiner/backend`

**Common misconfig:** Root Directory = `` (repo root) → build uses root `Dockerfile` → runs **EngageFlow** (Python), not Joiner. That would not serve `{"service":"joiner"}` on GET / — so current run is Joiner Node, but likely **old** code (main) if sync is 404.

**Exact fix:** Set **Root Directory** to `joiner/backend`. Branch = `dev`. Redeploy.

---

## PHASE 4 — ROUTE REGISTRATION PROOF

**1) Health**
```bash
curl -sS https://joiner-dev.up.railway.app/
# Expected: {"status":"ok","service":"joiner","api":"/api/profiles"}
```

**2) Version header (no debug flag)**
```bash
curl -sS -i https://joiner-dev.up.railway.app/ | grep -i x-joiner-git-sha
```

**3) Routes (requires ENGAGEFLOW_DEBUG=1 on Joiner)**
```bash
curl -sS https://joiner-dev.up.railway.app/debug/routes | jq .
```
Expected: `routes` array includes `{ "method": "POST", "path": "/internal/joiner/sync-cookies" }`.

**4) Sync endpoint**
```bash
curl -i -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://joiner-dev.up.railway.app/internal/joiner/sync-cookies
```
Expected: `HTTP/2 200` and JSON `{ "success": true, "scanned": 3, "updated": N }`.

---

## PHASE 5 — OUTPUT CHECKLIST

1. **Screenshot/text of Joiner Source:** Repo, Branch = dev, Root Directory = joiner/backend
2. **Build log:** Deployed commit SHA (or X-Joiner-Git-Sha header)
3. **What was changed:** Root Directory → `joiner/backend`; Branch → `dev`
4. **curl -i sync:** Must be 200, not 404
5. **If still 404:** Paste exact build/deploy log lines for the Joiner service

---

## Code changes in this audit (no app logic)

- **X-Joiner-Git-Sha** response header on all responses (from `RAILWAY_GIT_COMMIT_SHA`).
- **GET /debug/routes** (when `ENGAGEFLOW_DEBUG=1`) returns `{ git_sha, routes }` so we can confirm the sync route is registered.

Commit and push to dev, then set Joiner Root Directory = `joiner/backend`, Branch = dev, and redeploy.

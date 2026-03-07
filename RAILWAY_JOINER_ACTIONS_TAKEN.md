# Railway Joiner — Actions Taken via CLI

## What I Did (with Railway access)

1. **Verified link:** `railway status` → Project: efficient-ambition, Service: **joiner**, Environment: DEV ✓

2. **Set variable:** `railway variables --set "ENGAGEFLOW_DEBUG=1"` → ran successfully (no error).

3. **Triggered redeploy:** `railway redeploy -y` → completed (no output).

4. **Deployed from joiner/backend:**  
   `cd joiner/backend && railway up -d`  
   → "Indexing... Uploading... Build Logs: https://railway.com/project/..."  
   (Same again with `railway up -d -c`.)

## Current Live State (after actions)

- **https://joiner-dev.up.railway.app/**  
  - Returns `{"detail":"Not Found"}` and header `x-engageflow-git-sha: unknown`.  
  - That is **FastAPI/EngageFlow**-style response, not Joiner Express.

- **https://joiner-dev.up.railway.app/api/profiles**  
  - Returns `[]` (empty array).

- **https://engageflow-dev.up.railway.app/health**  
  - Returns `{"status":"ok","running":true}` (correct EngageFlow).

So **joiner-dev** is currently serving an app that looks like **EngageFlow** (Python), not Joiner (Node). Possible causes:

- The deploy from `railway up` (joiner/backend) failed or was superseded, and the active deployment is an old one that was built from the wrong context (e.g. repo root → EngageFlow Dockerfile).
- Or the **Joiner** service in Railway has **Source** set to the same repo but **Root Directory** empty (or wrong), so it builds the root Dockerfile (EngageFlow) and Joiner never runs.

## What the Railway UI must do

The **Joiner** service must be configured so it builds and runs **Joiner** only:

1. **Settings → Source**
   - **Branch:** `dev`
   - **Root Directory:** `joiner/backend`
   - Build: **Dockerfile** (so it uses `joiner/backend/Dockerfile`).

2. **Redeploy** after saving (and disable build cache if available).

The Railway CLI cannot set **Branch** or **Root Directory**; that has to be done in the dashboard. Until that is set, Joiner will keep building from the wrong context and the sync endpoint will not exist.

## Proof to re-run after UI fix

```bash
curl -sS -i https://joiner-dev.up.railway.app/ | grep -i x-joiner-git-sha
curl -sS https://joiner-dev.up.railway.app/debug/routes | jq '.git_sha, (.routes[]? | select(.path=="/internal/joiner/sync-cookies"))'
curl -i -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://joiner-dev.up.railway.app/internal/joiner/sync-cookies
```

Expected: Joiner returns `{"status":"ok","service":"joiner",...}` on GET `/`, header `X-Joiner-Git-Sha`, and sync returns 200.

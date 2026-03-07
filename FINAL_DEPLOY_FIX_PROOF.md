# Joiner Final Deploy Fix — Proof (Execute and Prove)

## Current Live State (as of run)

| Check | Result |
|-------|--------|
| X-Joiner-Git-Sha header | **MISSING** |
| GET /debug/routes | **404** Cannot GET /debug/routes |
| POST /internal/joiner/sync-cookies | **404** |

**Conclusion:** Railway Joiner is not running commit 0155f64. Branch and/or Root Directory not yet fixed.

---

## STEP 1 — Railway Source Settings (YOU DO THIS)

**Joiner service → Settings → Source**

Set exactly:

| Field | Value |
|-------|--------|
| Repo | `limdin25/engageflow` (or your fork) |
| Branch | `dev` |
| Root Directory | `joiner/backend` |
| Build | Dockerfile |

Save.

**Proof required:** Screenshot or copied text of the Source section showing repo, branch, root directory, build method.

```
[PASTE SCREENSHOT OR TEXT HERE]
```

---

## STEP 2 — Force Redeploy

Redeploy Joiner. If offered, use **Redeploy with build cache disabled**.

---

## STEP 3 — Build Log Proof (YOU COPY FROM RAILWAY)

**Deployments → Latest deployment**

Copy 5–15 lines that show:
- Branch = dev
- Commit SHA = 27f95a7 or 0155f64 or newer

**Build Logs** (same deployment):

Copy lines that show:
- Build context / root directory (e.g. "Building from joiner/backend" or "Root: joiner/backend")
- Dockerfile path (e.g. "Dockerfile" or "joiner/backend/Dockerfile")

```
[PASTE DEPLOYMENT LOG LINES HERE]

[PASTE BUILD LOG LINES HERE]
```

---

## STEP 4 — Live Proof: Version Header (RUN AFTER DEPLOY)

```bash
curl -sS -i https://joiner-dev.up.railway.app/ | grep -i x-joiner-git-sha
```

**Expected:** `x-joiner-git-sha: 0155f64...` (or current dev SHA)

**Current:** (no header)

---

## STEP 5 — Live Proof: Routes

Set **ENGAGEFLOW_DEBUG=1** on Joiner in Railway, redeploy if needed. Then:

```bash
curl -sS https://joiner-dev.up.railway.app/debug/routes | jq '.git_sha, (.routes[] | select(.path=="/internal/joiner/sync-cookies"))'
```

**Expected:** git_sha string and `{ "method": "POST", "path": "/internal/joiner/sync-cookies" }`

**Current:** 404 (endpoint not present)

---

## STEP 6 — Live Proof: Sync Endpoint

```bash
curl -i -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://joiner-dev.up.railway.app/internal/joiner/sync-cookies
```

**Expected:** `HTTP/2 200` and body `{ "success": true, "scanned": 3, "updated": N }`

**Current:** `HTTP/2 404`

---

## STEP 7 — Cleanup

Remove **ENGAGEFLOW_DEBUG=1** from Joiner. Redeploy.

---

## OUTPUT CHECKLIST (FILL AND RETURN)

| # | Item | Status / Proof |
|---|------|----------------|
| 1 | Source settings (repo/branch/rootdir/build) | [ ] Done — paste above |
| 2 | Deployment log (branch + commit SHA) | [ ] Paste above |
| 3 | Build log (rootdir + Dockerfile path) | [ ] Paste above |
| 4 | curl header (X-Joiner-Git-Sha) | [ ] Run curl, paste output |
| 5 | /debug/routes (sync-cookies entry) | [ ] Run curl, paste output |
| 6 | curl sync (HTTP 200) | [ ] Run curl, paste output |
| 7 | Debug cleanup | [ ] Removed ENGAGEFLOW_DEBUG=1 |

Until 1–3 are done in Railway and 4–6 show the expected outputs, the deploy fix is not complete.

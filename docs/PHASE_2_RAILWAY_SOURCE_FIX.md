# BLOCKER: Railway deploying old image — fix source settings (no code changes)

## Evidence

- **EngageFlow back** running SHA: `db35b1f` (later showed `unknown` after a deploy).  
- **Expected:** ≥ `c219091` (includes `/internal/backup-db`, `/internal/restore-db`, `cookie_json` migration).
- **Joiner** missing `POST /internal/joiner/sync-cookies` → deploying wrong build.

**API limitation:** The Railway GraphQL API **cannot set the GitHub branch** for a service.  
`ServiceInstanceUpdateInput` has `rootDirectory`, `source` (repo/image only), and build options — **no branch field**.  
Branch is only configurable in the **Railway dashboard** (Settings → Source).

---

## Action required (Railway UI)

For **each** service: **engageflow back**, **joiner** (joiner-old / joiner-dev):

### 1) Settings → Source

| Field | EngageFlow back | Joiner |
|-------|-----------------|--------|
| **Repo** | `limdin25/engageflow` | `limdin25/engageflow` |
| **Branch** | **`dev`** | **`dev`** |
| **Root directory** | **`backend`** | **`joiner/backend`** |
| **Build** | Dockerfile | Dockerfile |

If there is a “Disable build cache on next deploy” (or similar) option, enable it for the next deploy.

### 2) Redeploy

Trigger **Redeploy** for that service and wait for the build to finish.

### 3) Proof of correct deploy

**EngageFlow back:**

```bash
curl -i https://engageflow-dev-ec26.up.railway.app/health | grep -i x-engageflow-git-sha
# Must show SHA >= c219091 (e.g. c219091 or dbb59c2 or later)

curl -i -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://engageflow-dev-ec26.up.railway.app/internal/backup-db
# Must NOT be 404 (200 + binary tarball or 401 if secret wrong)
```

**Joiner:**

```bash
curl -i https://joiner-dev.up.railway.app/health
# Or root: curl -i https://joiner-dev.up.railway.app/

curl -i -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://joiner-dev.up.railway.app/internal/joiner/sync-cookies
# Must return 200 JSON (e.g. { "success": true, "scanned": N, "updated": M }), not HTML 404
```

### 4) Only after proofs pass

Rerun **Phase 2 restore** and **dbinfo**.  
The dbinfo error “no such column: cookie_json” indicates the migration was not applied; once the correct SHA is live, the migration in dev HEAD will run, then re-run `/debug/dbinfo`.

---

## Output to paste (after you do the UI steps)

1. **Source settings** — Screenshot or exact text of Settings → Source for **engageflow back** and for **joiner** (branch = `dev`, root dirs as above).
2. **Build log excerpt** — From Railway build logs: line showing **branch** and **commit** (e.g. “Building from ref dev”, “Commit: c219091” or similar).
3. **Health headers with SHAs** — Output of:
   - `curl -i https://engageflow-dev-ec26.up.railway.app/health | grep -i x-engageflow-git-sha`
4. **backup-db endpoint status** — Output of:
   - `curl -i -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://engageflow-dev-ec26.up.railway.app/internal/backup-db`  
   (expect not 404).
5. **sync-cookies status** — Output of:
   - `curl -i -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://joiner-dev.up.railway.app/internal/joiner/sync-cookies`  
   (expect 200 + JSON).

---

## What was tried via API (no UI)

- **serviceInstanceUpdate** — Set `rootDirectory` to `backend` (engageflow back) and confirmed `joiner/backend` (joiner). **Branch cannot be set** (not in `ServiceInstanceUpdateInput`).
- **githubRepoDeploy** — Called with `branch: "dev"`, `repo: "limdin25/engageflow"`, `projectId`, `environmentId`. Returned a deployment ID; a new SUCCESS deployment appeared for engageflow back, but health then showed `x-engageflow-git-sha: unknown` and `/internal/backup-db` still returned 404. So either the deploy did not use the dev branch or the build did not include the latest commits. **Fixing the configured branch in the UI for each service remains required.**

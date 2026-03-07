# Joiner Build Source — Set Branch to dev (Dashboard Only)

## Blocker

Railway's public API **cannot set the GitHub branch** for a service.  
`ServiceInstanceUpdateInput` has `rootDirectory` and `source` (repo/image only).  
Branch is only configurable in the **Railway dashboard**.

## One-Time Fix (Railway Dashboard)

1. Open **Railway** → project **efficient-ambition** → service **Joiner**.
2. Go to **Settings** → **Source**.
3. Set:
   - **Repo:** `limdin25/engageflow`
   - **Branch:** `dev`  ← change if it shows `main`
   - **Root Directory:** `joiner/backend`
   - **Build:** Dockerfile (or detected)
4. **Save**.
5. Trigger **Redeploy** (Deployments → Redeploy, or leave and let next step do it via API).

## After Branch Is Set

From repo root (or `joiner/backend`):

```bash
# Trigger redeploy (builds from dev)
# Use Railway API or Dashboard "Redeploy"

# Then run proof script
cd joiner/backend && node scripts/run-live-proof.js
```

Or run the curls in **Proof bundle** below manually.

## Source Settings (Exact Text for Dashboard)

After opening Joiner → Settings → Source, confirm or set:

| Field | Value |
|-------|--------|
| Repo | `limdin25/engageflow` |
| Branch | `dev` |
| Root Directory | `joiner/backend` |
| Build | Dockerfile |

Save. Then trigger Redeploy (or use API: `serviceInstanceRedeploy` for Joiner).

## Proof Bundle (Run After Deploy from dev)

**Deployment:** Joiner, status SUCCESS (note deployment id from Railway).

**1) Fingerprint**
```bash
curl -i https://joiner-dev.up.railway.app/
```
Expect header: `X-Joiner-Git-Sha: <sha or unknown>`.

**2) db-info**
```bash
curl -sS "https://joiner-dev.up.railway.app/internal/joiner/debug/db-info" \
  -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET"
```
Expect JSON: `db_kind`, `db_path`, `profiles_has_cookie_json: true`, `profiles_columns` includes `cookie_json`.

**3) Failing profile (no cookies)**  
If profile `d56f73d2-08bc-4412-a018-960fe89362ad` has no cookies:
```bash
curl -sS "https://joiner-dev.up.railway.app/api/profiles/d56f73d2-08bc-4412-a018-960fe89362ad/skool-auth"
```
Expect: `"valid": false`, `"code": "NO_COOKIE_JSON"` (or `EMPTY_COOKIE_LIST`).

**4) With-cookies profile**
```bash
curl -sS "https://joiner-dev.up.railway.app/api/profiles/716e152e-eb1b-4282-9e9a-7eb8714a579d/skool-auth"
```
Expect: `valid: true` or `code: "COOKIE_EXPIRED"`.

## API Used (No Branch)

- `serviceInstanceUpdate(input: { rootDirectory: "joiner/backend" })` — applied.
- `serviceInstanceRedeploy(serviceId, environmentId)` — used to redeploy.
- `githubRepoDeploy(input: { projectId, environmentId, repo: "limdin25/engageflow", branch: "dev" })` — triggers a deploy from dev but does **not** change the service's configured branch; which service gets the deploy may vary.

**Conclusion:** Set **Branch = dev** in Railway dashboard for Joiner, then redeploy and run the proof bundle.

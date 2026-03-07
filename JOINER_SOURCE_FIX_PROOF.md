# Joiner Source Config Fix — Proof

## 1) Source settings (Railway API)

**Done via Railway GraphQL API** (no UI; Hugo did not click anything):

- **Endpoint:** `https://backboard.railway.com/graphql/v2`
- **Mutation:** `serviceInstanceUpdate(serviceId, environmentId, input: { rootDirectory: "joiner/backend" })`
- **Result:** `{ "data": { "serviceInstanceUpdate": true } }`

**Token for API:** Account token in `~/.railway/config.json` under **`.user.token`** (not at root). Use for Authorization: Bearer in GraphQL requests.

**Joiner service IDs (from existing `~/.railway/config.json` link):**

- Project: efficient-ambition (`f2cddd1a-3d44-47f6-bd18-5ce566b88da4`)
- Environment: DEV (`d488f841-2357-4946-98f1-5b7af137b17f`)
- Service: joiner (`50e311ec-ab40-4467-85c2-989b009b1829`)

**Redeploy:** `serviceInstanceRedeploy(serviceId, environmentId)` → `true`. New deployment built and reached **SUCCESS** (22:01:38 UTC).

---

## 2) Build / deployment

- **Latest deployment:** BUILDING → DEPLOYING → **SUCCESS** (created 2026-03-04T21:59:34Z).
- Root directory is now **joiner/backend** (set via API). Build context and Dockerfile path are therefore **joiner/backend** and **joiner/backend/Dockerfile** for that deployment.

*Build log excerpt:* Not copied from dashboard. To confirm in UI: Joiner → Deployments → latest → Build Logs; you should see branch (e.g. dev), commit SHA, and context/root **joiner/backend**.

---

## 3) Live service proof (curl)

### 1) Service identity

```bash
curl -sS https://joiner-dev.up.railway.app/
```

**Result:**

```json
{"status":"ok","service":"joiner","api":"/api/profiles"}
```

*(Note: `/health` is not implemented; root `/` is the service identity.)*

### 2) Profiles endpoint

```bash
curl -sS https://joiner-dev.up.railway.app/api/profiles | head -c 200
```

**Result:** JSON array of profiles (e.g. `[{"id":"716e152e-...","name":"...","email":"...",...}]`). This is the **Node Joiner** app, not EngageFlow (which would return `[]` or `{"detail":"Not Found"}`).

### 3) Version header

```bash
curl -sS -i https://joiner-dev.up.railway.app/ | grep -i x-joiner-git-sha
```

**Result:** No header in response. Joiner only sets `X-Joiner-Git-Sha` when `RAILWAY_GIT_COMMIT_SHA` or `ENGAGEFLOW_GIT_SHA` is set. If Railway does not inject `RAILWAY_GIT_COMMIT_SHA` for this service, the header will be absent; the app is still the correct Joiner service.

### 4) Sync endpoint

```bash
curl -i -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://joiner-dev.up.railway.app/internal/joiner/sync-cookies
```

**Result:** **HTTP 401** with `{"error":"Unauthorized"}` when `ENGAGEFLOW_JOINER_SECRET` is empty or wrong. That proves:

- The route **exists** (no 404).
- The running app is **Joiner** (Express), which checks the secret and returns 401 instead of EngageFlow’s 404.

With the correct `ENGAGEFLOW_JOINER_SECRET` set in Joiner’s Railway variables and passed in the header, the expected response is **HTTP 200** and `{ "success": true, "scanned": 3, "updated": N }`.

---

## 4) Confirmation

**Joiner is now the running service at https://joiner-dev.up.railway.app:**

- GET `/` → `{"status":"ok","service":"joiner","api":"/api/profiles"}`.
- GET `/api/profiles` → profile list from Node Joiner (not EngageFlow).
- POST `/internal/joiner/sync-cookies` → 401 without valid secret (route present; with correct secret → 200 and sync result).

The Joiner service was fixed by setting **Root Directory** to **joiner/backend** via the Railway GraphQL API and redeploying. No dashboard UI was required from Hugo.

---

## 5) Cleanup

**ENGAGEFLOW_DEBUG:** Was not added in this run. If it was previously set for debugging, remove it from Joiner’s variables in Railway and redeploy when you no longer need `/debug/routes`.

---

## 6) Reproducing the API fix

To re-apply the same source change (e.g. after a reset):

1. Ensure you are logged in: `railway login` (token in `~/.railway/config.json`).
2. Use the GraphQL mutation with the same `serviceId` and `environmentId` as above, and `input: { rootDirectory: "joiner/backend" }`.
3. Call `serviceInstanceRedeploy(serviceId, environmentId)` to deploy.

The file `scripts/railway-joiner-source-update.json` holds the mutation and variables (IDs only; no secrets). The token is read from `~/.railway/config.json` when running API calls.

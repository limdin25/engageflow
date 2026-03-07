# Joiner Deploy to Railway — Proof Bundle

## 1) Code on GitHub dev

- **Fetched:** `origin/dev`
- **Commit deployed:** `98dc055` — `joiner: db-info route, cookie_json migration, auth codes NO_COOKIE_JSON/COOKIE_EXPIRED`
- **Verified:** Commit includes:
  - `joiner/backend/server.js` — route `GET /internal/joiner/debug/db-info`, skool-auth returns `code`
  - `joiner/backend/db.js` — idempotent migration `ALTER TABLE profiles ADD COLUMN cookie_json TEXT`, fail-fast, startup log
  - `joiner/backend/db-info.js`, `joiner/backend/cookieBuilder.js`, etc.

**Remote ref:** `git ls-remote origin dev` → `98dc055e5643926331076df37fa0bc6e1645dfe4`

---

## 2) Railway redeploy triggered

- **API:** `serviceInstanceRedeploy(serviceId, environmentId)` — success.
- **Root directory re-applied:** `serviceInstanceUpdate(input: { rootDirectory: "joiner/backend" })` — success.
- **Deployments:** Multiple redeploys triggered; latest **SUCCESS** deployment id: `7bf66f7f-e712-41d4-bcb2-f94e98d80339` (and after root dir re-apply, another SUCCESS).

---

## 3) Live proof (current state)

**Fingerprint**
```bash
curl -i https://joiner-dev.up.railway.app/
```
**Result:** `HTTP/2 200`, body `{"status":"ok","service":"joiner","api":"/api/profiles"}`.  
**X-Joiner-Git-Sha:** Not present in response (Railway may not set `RAILWAY_GIT_COMMIT_SHA` for this service, or build is from older commit).

**db-info**
```bash
curl -sS "https://joiner-dev.up.railway.app/internal/joiner/debug/db-info" \
  -H "X-JOINER-SECRET: <redacted>"
```
**Result:** `404 Cannot GET /internal/joiner/debug/db-info` — route not present in running image.

**Failing profile skool-auth**
```bash
curl -sS "https://joiner-dev.up.railway.app/api/profiles/d56f73d2-08bc-4412-a018-960fe89362ad/skool-auth"
```
**Result:** `{"valid":false,"error":"No cookies"}` — **no `code` field** (old response shape).

**With-cookies profile skool-auth**
```bash
curl -sS "https://joiner-dev.up.railway.app/api/profiles/716e152e-eb1b-4282-9e9a-7eb8714a579d/skool-auth"
```
**Result:** `{"valid":true,"user":{...}}` — OK.

---

## 4) Blocker — build not from dev

Evidence shows the **running Joiner image does not contain commit 98dc055**:
- `/internal/joiner/debug/db-info` returns 404.
- skool-auth does not return `code: "NO_COOKIE_JSON"`.

**Likely cause:** Joiner service in Railway is building from branch **main** (or a cached build), not **dev**. Root directory was re-applied via API; **branch cannot be set via API** and must be set in the Railway dashboard.

**Required fix (Railway dashboard):**
1. Joiner service → **Settings** → **Source**
2. Set **Branch** to **dev**
3. **Root Directory** to **joiner/backend** (already set via API; confirm in UI)
4. Save and **Redeploy** (or trigger redeploy after saving).

After the next build from **dev** (98dc055 or later), re-run the proofs below.

---

## 5) Expected proof after building from dev

**Commit hash deployed:** `98dc055` (or later on dev).

**curl -i /**
- Header: `X-Joiner-Git-Sha: <sha or unknown>`
- Body: `{"status":"ok","service":"joiner","api":"/api/profiles"}`

**db-info (redacted):**
```json
{
  "db_kind": "sqlite",
  "db_path": "engageflow.db",
  "resolved_path": "/data/engageflow.db",
  "schema_hash": "<16-char hex>",
  "tables": ["browser_locks", "profiles", ...],
  "profiles_columns": ["id", "name", ..., "cookie_json"],
  "profiles_has_cookie_json": true
}
```

**Failing profile:**
```json
{"valid":false,"error":"No cookies","code":"NO_COOKIE_JSON"}
```

**With-cookies profile:**  
`{"valid":true,"user":{...}}` or `{"valid":false,"code":"COOKIE_EXPIRED",...}` if Skool returns 401/403.

**Railway deployment:** Status **SUCCESS**; deployment id from latest build from dev.

---

## 6) Commands to re-run after dashboard fix

```bash
# Fingerprint
curl -i https://joiner-dev.up.railway.app/

# db-info (set ENGAGEFLOW_JOINER_SECRET or use redacted placeholder)
curl -sS "https://joiner-dev.up.railway.app/internal/joiner/debug/db-info" \
  -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET"

# Auth codes (use profile without cookies for NO_COOKIE_JSON proof)
curl -sS "https://joiner-dev.up.railway.app/api/profiles/aa599316-f52c-4428-94df-4d101078c765/skool-auth"
curl -sS "https://joiner-dev.up.railway.app/api/profiles/716e152e-eb1b-4282-9e9a-7eb8714a579d/skool-auth"
```

**No-cookie profile id:** `aa599316-f52c-4428-94df-4d101078c765` (from GET /api/profiles, has_cookie_json false). After deploy from dev, skool-auth for this id must return `"code":"NO_COOKIE_JSON"`.

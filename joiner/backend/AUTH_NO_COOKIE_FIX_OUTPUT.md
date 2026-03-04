# Fix “Auth failed: No cookie” — Output

## 1) Failing profile ids

- **Profile without cookies (triggers NO_COOKIE_JSON):** `d56f73d2-08bc-4412-a018-960fe89362ad`
- **Profile with cookies (for comparison):** `716e152e-eb1b-4282-9e9a-7eb8714a579d`

**Reproduced:** `GET /api/profiles/:id/skool-auth` for the no-cookie profile returns `{"valid":false,"error":"No cookies"}`. After this fix it returns `{"valid":false,"error":"No cookies","code":"NO_COOKIE_JSON"}` and the log line includes `profile_id`, `email`, and `request=GET https://api2.skool.com/self`.

---

## 2) DB proof (sanitized) — source of truth

**Joiner DB source of truth:** EngageFlow DB (`ENGAGEFLOW_DB_PATH`). Joiner reads/writes `profiles` (and `browser_locks`) there. Local: `config.js` → `../../backend/engageflow.db`. Railway: `ENGAGEFLOW_DB_PATH` → `/data/engageflow.db`.

**Runtime DB identification:** `GET /internal/joiner/debug/db-info` (header `X-JOINER-SECRET`). Returns `db_kind`, `db_path` (basename), `resolved_path`, `schema_hash`, `tables`, `profiles_columns`, `profiles_has_cookie_json`. No secrets.

**Migration:** On startup, Joiner ensures `profiles.cookie_json` exists (idempotent `ALTER TABLE profiles ADD COLUMN cookie_json TEXT` if missing). If column still missing after migration, startup fails with: `Joiner requires profiles.cookie_json. DB schema missing required column.`

**Local:** After migration, local `backend/engageflow.db` has `cookie_json`; `db-cookie-proof.js` runs and prints per-profile stats when profiles exist. **Railway:** After deploy, call db-info to confirm `profiles_has_cookie_json: true` and same schema expectations.

**Script:** `joiner/backend/scripts/db-cookie-proof.js`. Run from `joiner/backend`: `node scripts/db-cookie-proof.js`. When DB has `cookie_json`, prints per profile: `id`, `email` (truncated), `cookie_json_exists`, `cookie_json_non_empty`, `cookie_json_parses`, `cookie_count`, `first_2_names` (names only, no values).

---

## 3) Code diff summary

| File | Change |
|------|--------|
| **joiner/backend/cookieBuilder.js** (new) | Parses `cookie_json` (array or `{ cookies: [] }`), builds Cookie header, returns `NO_COOKIE_JSON` / `EMPTY_COOKIE_LIST`. Debug log: `cookie_json_len`, `cookie_count`, `first_2_names` (no values). |
| **joiner/backend/skoolLogin.js** | `validateCookies` uses `buildCookieHeader`; returns `code`: `NO_COOKIE_JSON`, `EMPTY_COOKIE_LIST`, `COOKIE_EXPIRED` (on HTTP 401/403), `REQUEST_ERROR` on throw. Optional `meta` for debug log. |
| **joiner/backend/skoolApi.js** | `skoolRequest` uses `buildCookieHeader` for consistent parsing and logging. |
| **joiner/backend/server.js** | **skool-auth:** If no/empty `cookie_json` → `{ valid: false, code: 'NO_COOKIE_JSON' }` and `writeLog` with `profile_id`, `email`, `request=GET https://api2.skool.com/self`. On failure, store `result.code` in `auth_error` and log with profile_id/email. **GET /api/profiles:** Effective status: if DB `status === 'ready'` and `!hasCookies` → expose `status: 'paused'`. |
| **joiner/src/components/AccountsTab.tsx** | Test auth alert: show “Cookie expired — re-export cookies…” when `result.code === 'COOKIE_EXPIRED'`; otherwise show `result.code || result.error`. Profile detail: show “Cookie expired — re-export required” when `auth_error === 'COOKIE_EXPIRED'`. |

---

## 4) Test results

```bash
cd joiner/backend && node cookieBuilder.test.js
```

- Valid array `cookie_json` → non-empty Cookie header, correct count and names.
- Object with `cookies` array → non-empty header.
- Missing / empty string / empty array / invalid JSON → `NO_COOKIE_JSON` or `EMPTY_COOKIE_LIST`.
- `parseCookieJson` exposes codes.

All cookieBuilder tests passed.

---

## 5) Final proof (after deploy)

**Before deploy (current live):**  
`curl -sS "https://joiner-dev.up.railway.app/api/profiles/d56f73d2-08bc-4412-a018-960fe89362ad/skool-auth"`  
→ `{"valid":false,"error":"No cookies"}` (no `code`).

**After deploy:** Same URL must return:
- `{"valid":false,"error":"No cookies","code":"NO_COOKIE_JSON"}`

Log line must include: `Auth failed: NO_COOKIE_JSON profile_id=d56f73d2-08bc-4412-a018-960fe89362ad email=... request=GET https://api2.skool.com/self`.

**Cookie expired (401/403 from Skool):** Response will be `{"valid":false,"error":"cookie_expired","code":"COOKIE_EXPIRED"}`; profile `auth_error` set to `COOKIE_EXPIRED`; UI shows “Cookie expired — re-export required”.

**Reclassification:** “Auth failed: No cookie” is replaced by:
- **NO_COOKIE_JSON** when profile has no or empty `cookie_json`.
- **EMPTY_COOKIE_LIST** when `cookie_json` parses but yields zero valid name/value cookies.
- **COOKIE_EXPIRED** when Skool returns 401/403 (cookies expired).

No secrets or cookie values are logged; only cookie names and counts.

---

## 6) Joiner DB source of truth (db-info proof)

**Endpoint:** `GET /internal/joiner/debug/db-info` with header `X-JOINER-SECRET: <secret>`.

**Local output (after migration):**
```json
{
  "db_kind": "sqlite",
  "db_path": "engageflow.db",
  "resolved_path": "/Users/.../engageflow-repo/backend/engageflow.db",
  "schema_hash": "a927a6e317083965",
  "tables": ["activity_feed", "browser_locks", "profiles", ...],
  "profiles_columns": ["id", "name", ..., "cookie_json"],
  "profiles_has_cookie_json": true
}
```

**Railway (after deploy):** Call same endpoint on `https://joiner-dev.up.railway.app/internal/joiner/debug/db-info`. Expect `db_path: "engageflow.db"`, `profiles_has_cookie_json: true`. If false, migration runs on next deploy; backfill is idempotent (ALTER TABLE ADD COLUMN if missing).

**Final verification:** For profile without cookies, `GET /api/profiles/<id>/skool-auth` returns `{"valid":false,"code":"NO_COOKIE_JSON"}`. After cookies added (paste or sync), returns `valid: true`.

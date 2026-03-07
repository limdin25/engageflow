# Phase 2 — Joiner cookie sync fix (match by email, dedupe)

## What was implemented

### EngageFlow backend (`backend/app.py`)

- **GET /internal/joiner/profiles-cookies** (X-JOINER-SECRET)  
  Returns `{ "profiles": [ { "email", "cookie_json" }, ... ] }` for all profiles with non-empty `cookie_json`. Used by Joiner to sync by email.
- **GET /internal/joiner/debug-profiles** (X-JOINER-SECRET)  
  Returns `{ "rows": [ { "email", "cookie_json_length" }, ... ] }` (no cookie content). Equivalent to `SELECT email, LENGTH(cookie_json) FROM profiles`.
- **Refactor:** `_require_joiner_secret(request)` used for all internal joiner routes.

### Joiner (`joiner/backend/server.js`)

- **sync-cookies** now:
  1. Calls **dedupeProfilesByEmail()** — keeps one row per `LOWER(TRIM(email))` (newest by `rowid`), deletes duplicates.
  2. Fetches **GET EngageFlow /internal/joiner/profiles-cookies** (not per-profile by id).
  3. Updates local DB with **`UPDATE profiles SET cookie_json = ? WHERE LOWER(TRIM(COALESCE(email, ""))) = LOWER(TRIM(?))`** so casing/whitespace don’t block matches.
- **dedupeProfilesByEmail()** — removes duplicate profile rows by email (keeps newest per email).

## Verification (run after both services are deployed from latest `dev`)

Secret and URLs (set once):

```bash
# Get secret from Railway → joiner (joiner-dev-abdb) → Variables → ENGAGEFLOW_JOINER_SECRET
export ENGAGEFLOW_JOINER_SECRET='<value>'
```

1. **EngageFlow profiles query** (email + LENGTH(cookie_json)):

   ```bash
   curl -sS -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
     https://engageflow-dev-ec26.up.railway.app/internal/joiner/debug-profiles | jq .
   ```

   Expected: 3 rows with non-null `cookie_json_length`.

2. **Joiner profiles query** (email only):

   ```bash
   curl -sS https://joiner-dev-abdb.up.railway.app/api/profiles | jq '.[].email'
   ```

   After dedupe: 3 emails (no duplicates).

3. **Sync cookies**:

   ```bash
   curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
     https://joiner-dev-abdb.up.railway.app/internal/joiner/sync-cookies | jq .
   ```

   Expected: `updated: 3` (or at least > 0).

4. **Final profiles table**:

   ```bash
   curl -sS https://joiner-dev-abdb.up.railway.app/api/profiles | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'
   ```

   Expected: `has_cookie_json: true`, `auth_status: "connected"` for the 3 cookie accounts.

## Current run (before EngageFlow deploy of new routes)

- **EngageFlow** was still on previous image: `/internal/joiner/profiles-cookies` and `/internal/joiner/debug-profiles` returned **404**. Redeploy was triggered; once the new image is live, re-run the four steps above.
- **Joiner** (after deploy): dedupe already reduced to 3 emails; sync returned `skipped: "http 401"` because the fetch to EngageFlow’s new endpoint failed (404/401 until EngageFlow serves the new code).

### Outputs from last run

**1. EngageFlow profiles query:**  
`{"detail":"Not Found"}` (new route not deployed yet).

**2. Joiner profiles query (email only):**
```
"hugords100+1@gmail.com"
"hugords100@gmail.com"
"marknoah2024@gmail.com"
```
(3 rows after dedupe.)

**3. Sync cookies:**
```json
{ "success": true, "scanned": 0, "updated": 0, "skipped": "http 401" }
```

**4. Final profiles table:**
```json
{"email": "hugords100+1@gmail.com", "has_cookie_json": false, "auth_status": "disconnected"}
{"email": "hugords100@gmail.com", "has_cookie_json": false, "auth_status": "disconnected"}
{"email": "marknoah2024@gmail.com", "has_cookie_json": false, "auth_status": "disconnected"}
```

After **EngageFlow** is deployed from commit **aead079** (or later dev), run the four curl commands again; then you should see `debug-profiles` with 3 rows, sync `updated: 3`, and profiles with `has_cookie_json: true`, `auth_status: "connected"`.

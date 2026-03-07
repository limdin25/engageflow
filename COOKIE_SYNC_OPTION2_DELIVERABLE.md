# EngageFlow Option 2: Cookie Sync API — Deliverable

## 1) Baseline Commits

| Repo/Service | Commit | Message |
|--------------|--------|---------|
| EngageFlow | `cf564c3` | baseline: before cookie sync api |
| Joiner | `c8866d0` | baseline: before cookie sync pull |

## 2) EngageFlow Commit + Endpoints Added

**Commit:** `4ff2a32` — `engageflow: add internal cookie sync endpoint for joiner (secret-gated)`

**Endpoint:**
- `GET /internal/joiner/profiles/{profile_id}/cookie`
- **Auth:** Header `X-JOINER-SECRET` must equal `ENGAGEFLOW_JOINER_SECRET`
- **Response:**
  - `200 { "cookie_json": "<string>" }` if profile has cookies
  - `200 { "cookie_json": null }` if profile has no cookies
  - `401` if header missing or wrong secret
- **Logging:** Only `profile_id` and `has_cookie` boolean; never logs `cookie_json`

## 3) Joiner Commit + Sync Behavior

**Commit:** `9baef8c` — `joiner: pull cookie_json from engageflow internal api (secret-gated)`

**Changes:**
- **Config:** `ENGAGEFLOW_INTERNAL_URL`, `ENGAGEFLOW_JOINER_SECRET` in `config.railway.js`
- **Sync function:** `syncCookiesFromEngageFlow()` in `server.js`
  - Fetches each profile's cookie from EngageFlow internal endpoint
  - Updates Joiner DB when EngageFlow has cookies and Joiner does not
  - Concurrency: 3 at a time, 10s timeout, 1 retry
- **Triggers:**
  - On Joiner startup (when `RAILWAY=true`)
  - `POST /internal/joiner/sync-cookies` (secret-gated) for manual trigger
- **API:** `GET /api/profiles` returns `has_cookie_json` instead of `cookie_json` (never exposes cookies to frontend)
- **Frontend:** `AccountsTab.tsx` uses `has_cookie_json` for status display; Reveal shows "Cookies present (hidden for security)" instead of raw value

## 4) Railway Env Var Checklist

### EngageFlow Service
| Variable | Value | Required |
|----------|-------|----------|
| `ENGAGEFLOW_JOINER_SECRET` | `<random-long-secret>` (e.g. 32+ chars) | Yes |
| `ENGAGEFLOW_DEBUG` | `1` (optional, for /debug/dbinfo) | No |

### Joiner Service
| Variable | Value | Required |
|----------|-------|----------|
| `ENGAGEFLOW_INTERNAL_URL` | `https://engageflow-dev.up.railway.app` | Yes |
| `ENGAGEFLOW_JOINER_SECRET` | Same value as EngageFlow | Yes |
| `ENGAGEFLOW_DEBUG` | `1` (optional) | No |

**Important:** Both services must use the **same** `ENGAGEFLOW_JOINER_SECRET`.

## 5) Verification Evidence

### 5.1 EngageFlow endpoint denies unauthorized
```bash
# No header -> 401
curl -sS -o /dev/null -w "%{http_code}" https://engageflow-dev.up.railway.app/internal/joiner/profiles/<profile_id>/cookie
# Expected: 401

# Wrong secret -> 401
curl -sS -o /dev/null -w "%{http_code}" -H "X-JOINER-SECRET: wrong" https://engageflow-dev.up.railway.app/internal/joiner/profiles/<profile_id>/cookie
# Expected: 401

# Correct secret -> 200 (do NOT print cookie contents)
curl -sS -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://engageflow-dev.up.railway.app/internal/joiner/profiles/<profile_id>/cookie | jq 'keys'
# Expected: ["cookie_json"]
```

### 5.2 Trigger Joiner cookie sync
- **Option A:** Restart Joiner service (sync runs on startup)
- **Option B:** `POST /internal/joiner/sync-cookies` with header `X-JOINER-SECRET`

### 5.3 Verify Joiner profiles have cookies
```bash
curl -sS https://joiner-dev.up.railway.app/api/profiles | jq '.[] | {email, has_cookie_json, auth_status}'
```
**Expected:** Accounts with cookies in EngageFlow show `has_cookie_json: true` and `auth_status: "connected"`.

### 5.4 UI behavior
- Hard refresh Communities → Join → Accounts
- Accounts with cookies become **Connected** automatically without clicking Test Auth

## 6) Success / Fail

| Check | Result |
|-------|--------|
| EngageFlow 401 without header | |
| EngageFlow 401 with wrong secret | |
| EngageFlow 200 with correct secret | |
| Joiner sync on startup | |
| Joiner profiles show has_cookie_json | |
| UI auto-connects accounts | |

## 7) Rollback Steps

1. **Remove env vars from Railway:**
   - EngageFlow: remove `ENGAGEFLOW_JOINER_SECRET`
   - Joiner: remove `ENGAGEFLOW_INTERNAL_URL`, `ENGAGEFLOW_JOINER_SECRET`

2. **Revert commits** (both in same repo, newest first):
   ```bash
   git revert 9baef8c  # Joiner
   git revert 4ff2a32  # EngageFlow
   ```

3. **Redeploy both services**

4. **Verify:** Joiner falls back to manual Connect/Paste; no sync attempted when env vars missing.

# Cookie Sync Option 2 — Phase 4–5 Proof

## Pre-requisite: Deploy Status

**Current live state (verified):**
- EngageFlow `/internal/joiner/profiles/{id}/cookie` → **401** (endpoint live; SHA bcc0e73)
- Joiner `/api/profiles` → returns `has_cookie_json` ✓

---

## 1) Railway Env Var Checklist

| Service | Variable | Value | Status |
|---------|----------|-------|--------|
| **EngageFlow** | `ENGAGEFLOW_JOINER_SECRET` | `<random-long-secret>` (32+ chars) | ☐ DONE |
| **EngageFlow** | `ENGAGEFLOW_DEBUG` | `1` (temporary) | ☐ DONE |
| **Joiner** | `ENGAGEFLOW_INTERNAL_URL` | `https://engageflow-dev.up.railway.app` | ☐ DONE |
| **Joiner** | `ENGAGEFLOW_JOINER_SECRET` | Same as EngageFlow | ☐ DONE |
| **Joiner** | `ENGAGEFLOW_DEBUG` | `1` (temporary) | ☐ DONE |

**Redeploy BOTH services after setting vars.**

---

## 2) Gate Proof (run after redeploy)

Profile IDs (from EngageFlow `/profiles`):
- `716e152e-eb1b-4282-9e9a-7eb8714a579d` (hugords100+1)
- `d56f73d2-08bc-4412-a018-960fe89362ad` (hugords100)
- `aa599316-f52c-4428-94df-4d101078c765` (marknoah2024)

### A) No header → 401
```bash
curl -i https://engageflow-dev.up.railway.app/internal/joiner/profiles/716e152e-eb1b-4282-9e9a-7eb8714a579d/cookie
```
**Expected:** `HTTP/1.1 401 Unauthorized`

### B) Wrong secret → 401
```bash
curl -i -H "X-JOINER-SECRET: wrong" https://engageflow-dev.up.railway.app/internal/joiner/profiles/716e152e-eb1b-4282-9e9a-7eb8714a579d/cookie
```
**Expected:** `HTTP/1.1 401 Unauthorized`

### C) Correct secret → 200
```bash
curl -sS -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://engageflow-dev.up.railway.app/internal/joiner/profiles/716e152e-eb1b-4282-9e9a-7eb8714a579d/cookie | jq 'if .cookie_json == null then "cookie_json: null" else "cookie_json: non-null" end'
```
**Expected:** `200` + `"cookie_json: non-null"` or `"cookie_json: null"` (do NOT paste actual cookie contents)

| Test | Expected | Actual |
|------|----------|--------|
| A) No header | 401 | 401 ✓ |
| B) Wrong secret | 401 | 401 ✓ |
| C) Correct secret | 200 | *(run with $ENGAGEFLOW_JOINER_SECRET)* |

---

## 3) Sync Proof

**Trigger:** `POST /internal/joiner/sync-cookies` with header `X-JOINER-SECRET: <secret>`

**Response:** `{ success: true, scanned: N, updated: M }` (no cookie contents)

```bash
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://joiner-dev.up.railway.app/internal/joiner/sync-cookies | jq .
```

**Alternative:** Joiner runs sync on startup when `RAILWAY=true` and env vars are set. Check Joiner logs for:
```
[cookie-sync] Synced cookies for N profile(s) from EngageFlow
```
or
```
[cookie-sync] Startup sync: N profile(s) updated
```

| Proof | Result |
|-------|--------|
| Sync endpoint exists | Yes (`POST /internal/joiner/sync-cookies`) |
| Returns scanned/updated | Yes (`{ scanned, updated }`) |
| Triggered on startup | Yes (when RAILWAY=true + env set) |

---

## 4) /api/profiles Proof

```bash
curl -sS https://joiner-dev.up.railway.app/api/profiles | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'
```

**Expected after sync:**
| email | has_cookie_json | auth_status |
|-------|-----------------|-------------|
| hugords100+1@gmail.com | true | connected |
| hugords100@gmail.com | true/false | connected/disconnected |
| marknoah2024@gmail.com | true/false | connected/disconnected |

*(hugords100 and marknoah depend on EngageFlow DB having cookies for them)*

---

## 5) UI Confirmation Notes

- Hard refresh: Communities → Join → Accounts
- Accounts with cookies: show **Connected** without clicking Test Auth
- No alerts, no cookie display (Reveal shows "Cookies present (hidden for security)")

---

## 6) Debug Cleanup

After proof, remove `ENGAGEFLOW_DEBUG=1` from both EngageFlow and Joiner services. Redeploy.

# Option 2 — Final Execution Run

**Date:** 2026-03-04

---

## 1. Deploy SHAs

| Service | Git SHA | Expected | Status |
|---------|---------|----------|--------|
| **EngageFlow** | `bcc0e73` | >= 01589a9 | ⚠️ Behind |
| **Joiner** | N/A | >= 9baef8c | ⚠️ No version header; sync 404 |

**Evidence:**
```
$ curl -sS -i https://engageflow-dev.up.railway.app/health | grep x-engageflow-git-sha
x-engageflow-git-sha: bcc0e733803e395f5cab85b80916701c863efd48
```

---

## 2. Cookie Endpoint Proof (Before Connect)

| email | cookie_json |
|-------|-------------|
| hugords100@gmail.com | **null** |
| marknoah2024@gmail.com | **null** |

**Expected:** Both null ✓

---

## 3. User Connect Action

**Manual step:** Communities → Join → Accounts — Connect for hugords100, then marknoah2024. Complete login. Do not run Test Auth.

---

## 4. Cookie Endpoint Proof (After Connect)

*(Re-run after Step 3)*

| email | cookie_json |
|-------|-------------|
| hugords100@gmail.com | *(pending user Connect)* |
| marknoah2024@gmail.com | *(pending user Connect)* |

**Expected after Connect:** non-null for both.

**Note:** EngageFlow at bcc0e73 lacks the PUT cookie endpoint (added in 01589a9). Joiner Connect cannot push cookies to EngageFlow until EngageFlow is redeployed.

---

## 5. Sync Endpoint Output

**Result:** `404 Cannot POST /internal/joiner/sync-cookies`

Joiner does not expose the sync endpoint. Redeploy Joiner from dev (9baef8c+) required.

**Expected when deployed:** `{ "success": true, "scanned": 3, "updated": 0|1|2 }`

---

## 6. /api/profiles Verification

**Current state:**

| email | has_cookie_json | auth_status |
|-------|-----------------|-------------|
| hugords100+1@gmail.com | true | connected |
| hugords100@gmail.com | false | disconnected |
| marknoah2024@gmail.com | false | disconnected |

**Expected after Connect + sync:** All three `true` | `connected`.

---

## 7. UI Confirmation

**Action:** Hard refresh → Communities → Join → Accounts.

**Expected:** All three accounts show **Connected** without Test Auth.

---

## 8. Debug Cleanup

Remove `ENGAGEFLOW_DEBUG=1` from both services. Redeploy.

---

## Summary

| Step | Result |
|------|--------|
| 1. Deploy SHAs | EngageFlow bcc0e73 (behind); Joiner unknown |
| 2. Cookie before Connect | Both null ✓ |
| 3. User Connect | Manual |
| 4. Cookie after Connect | Blocked until EngageFlow 01589a9 |
| 5. Sync | 404 — Joiner needs redeploy |
| 6. /api/profiles | 2/3 disconnected |
| 7. UI | Pending |
| 8. Debug cleanup | Pending |

**Blockers:** Redeploy EngageFlow to 01589a9 and Joiner to 9baef8c+ from `dev` branch.

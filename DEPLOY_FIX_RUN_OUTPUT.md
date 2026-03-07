# Option 2 — Deploy Fix Run Output

## Step 1: Local Commits ✓

```
27f95a7 chore: trigger Railway redeploy
01589a9 option2: EngageFlow PUT cookie endpoint + Joiner push on Connect/paste
9a30adc docs: blocker clear output + deploy fix evidence
bcc0e73 engageflow: add /debug/version (ENGAGEFLOW_DEBUG=1) for deploy verification
d354cba joiner: sync-cookies returns scanned/updated (no cookie contents)
9baef8c joiner: pull cookie_json from engageflow internal api (secret-gated)
4ff2a32 engageflow: add internal cookie sync endpoint for joiner (secret-gated)
...
```

**Confirmed:** 01589a9, 9baef8c, d354cba exist locally.

---

## Step 2: Push dev ✓

```
Everything up-to-date
27f95a79ea236c2272bc7a011e35c2fe6bf48d86	refs/heads/dev
```

**Remote origin/dev:** 27f95a7 (includes 01589a9, 9baef8c, d354cba)

---

## Step 3: Force Railway Redeploy

**Manual action required:** In Railway dashboard:

| Service | Branch | Action |
|---------|--------|--------|
| EngageFlow | dev | Trigger Redeploy |
| Joiner | dev | Trigger Redeploy |

---

## Step 4: Deployed SHAs (Current)

| Service | Deployed SHA | Expected |
|---------|--------------|----------|
| **EngageFlow** | `bcc0e73` | >= 01589a9 |
| **Joiner** | N/A | sync endpoint |

**Status:** Railway has not yet picked up the new commits. Manual redeploy (Step 3) required.

---

## Step 5: Sync Endpoint Status

**Current:** `404 Cannot POST /internal/joiner/sync-cookies`

**Expected after redeploy:** `200` with `{ success: true, scanned: 3, updated: N }`

---

## Step 6: Cookie Sync Output

**Current:** N/A (endpoint 404)

---

## Step 7: /api/profiles Table

| email | has_cookie_json | auth_status |
|-------|-----------------|-------------|
| hugords100+1@gmail.com | true | connected |
| hugords100@gmail.com | false | disconnected |
| marknoah2024@gmail.com | false | disconnected |

**Expected after Connect + sync:** All three `true` | `connected`.

---

## Summary

| Item | Status |
|------|--------|
| 1. Railway deployed SHAs | EngageFlow bcc0e73 (behind); Joiner unknown |
| 2. Sync endpoint status | 404 — needs redeploy |
| 3. Cookie sync output | N/A |
| 4. /api/profiles table | 2/3 disconnected |

**Next:** Trigger redeploy for both services in Railway dashboard (Step 3), then re-run verification.

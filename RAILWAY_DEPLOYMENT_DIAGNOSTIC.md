# Railway Deployment Diagnostic

## 1. Local Commit SHA

**Branch:** dev

**Latest commits:**
```
27f95a7 chore: trigger Railway redeploy
01589a9 option2: EngageFlow PUT cookie endpoint + Joiner push on Connect/paste
9a30adc docs: blocker clear output + deploy fix evidence
bcc0e73 engageflow: add /debug/version (ENGAGEFLOW_DEBUG=1) for deploy verification
d354cba joiner: sync-cookies returns scanned/updated (no cookie contents)
9baef8c joiner: pull cookie_json from engageflow internal api (secret-gated)
4ff2a32 engageflow: add internal cookie sync endpoint for joiner (secret-gated)
```

**Confirmed:** 01589a9, d354cba, 9baef8c exist on local dev.

---

## 2. Remote Commit SHA

| Branch | SHA |
|--------|-----|
| origin/dev | 27f95a79ea236c2272bc7a011e35c2fe6bf48d86 |
| origin/main | 2a8b986d7aff8eaf2f9ce95550fd5d04db93d001 |

**Local dev = origin/dev:** ✓ (27f95a7)

**main is behind:** main at 2a8b986 does NOT contain 9baef8c, d354cba, 01589a9.

---

## 3. Railway Configured Branch

**Evidence from docs:**
- `docs/OPTION1_FINISH_REPORT.md`: "Joiner is deployed from this repo (likely **main** branch for Railway-specific config)"
- `docs/PROJECT_STATE.md`: "Default branch: dev ← active engineering branch (GitHub repo default = main)"
- EngageFlow deploys from dev (proven: X-EngageFlow-Git-Sha = 27f95a7)
- Joiner sync endpoint 404 → Joiner does not have 9baef8c → Joiner deploys from **main**

**Inferred config:**

| Service | Repo | Branch | Deployed SHA |
|---------|------|--------|--------------|
| EngageFlow | engageflow (monorepo) | dev | 27f95a7 ✓ |
| Joiner | engageflow (monorepo) | **main** | 2a8b986 (no sync endpoint) |

---

## 4. Railway Deployed SHA

**EngageFlow:**
```
$ curl -sS -i https://engageflow-dev.up.railway.app/health | grep X-EngageFlow-Git-Sha
x-engageflow-git-sha: 27f95a79ea236c2272bc7a011e35c2fe6bf48d86
```
**Deployed:** 27f95a7 ✓ (>= 01589a9)

**Joiner:** No version header. Sync endpoint returns 404 → code is from main (2a8b986).

---

## 5. Root Cause

**Case A) Railway deploying wrong branch**

Joiner service is configured to deploy from **main**. main is at 2a8b986 and does not contain:
- 9baef8c (joiner cookie pull, sync endpoint)
- d354cba (sync-cookies returns scanned/updated)
- 01589a9 (cookie push)

EngageFlow deploys from **dev** (27f95a7) and is correct.

---

## 6. Exact Fix

**In Railway dashboard:**

1. Open project **efficient-ambition** (or your Railway project)
2. Select **Joiner** service
3. Go to **Settings** → **Source**
4. Change **Branch** from `main` to `dev`
5. Click **Redeploy** (or trigger deploy)

**Alternative (if branch setting is per-project):** Ensure Joiner service uses `dev` as its deploy branch.

**Verification after fix:**
```bash
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://joiner-dev.up.railway.app/internal/joiner/sync-cookies
```
Expected: `200` with `{ "success": true, "scanned": 3, "updated": N }`

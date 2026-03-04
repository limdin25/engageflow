# EngageFlow 404 Fix — Deployment Target

## Phase 1: Evidence of Deployed SHA (Before Fix)

**Method:** `X-EngageFlow-Git-Sha` response header (present on all responses)

```bash
curl -sS -i https://engageflow-dev.up.railway.app/health | grep -i x-engageflow-git-sha
```

**Result:** `x-engageflow-git-sha: f495b45eedbcb4be1d95ef7829d9bf811f397607`

**Commit:** `f495b45` — "fix: align countdown with VPS working clone — queue-first (Entry #40)"

**Target:** `4ff2a32` — "engageflow: add internal cookie sync endpoint for joiner (secret-gated)"

**Verdict:** `4ff2a32` is NOT an ancestor of `f495b45`. Deployed code is 10+ commits behind.

---

## Phase 2: Root Cause

**Evidence:**
- `origin/dev` has: 73dcdc7, ba82413, 4dce36f, ea52715 (only 4 commits)
- local `dev` has: d354cba, 9baef8c, 4ff2a32, ... (cookie sync work)
- `f495b45` exists only on local `dev`; origin was overwritten (4dce36f "OVERWRITE: Replace with correct code from Contabo VPS")

**Cause:** Railway deploys from the connected Git repo (likely `origin/dev`). Either:
1. Railway deployed from an old cached build (f495b45) that predates the overwrite, and never redeployed
2. Or Railway watches a branch that has diverged — local dev has cookie sync never pushed

**Fix:** Push local `dev` (with 4ff2a32) to `origin` and trigger redeploy.

---

## Phase 3: Endpoint Live (After Fix)

**Deployed SHA:** `bcc0e73` (contains 4ff2a32)

| Test | Expected | Actual |
|------|----------|--------|
| No header | 401 | 401 ✓ |
| Wrong secret | 401 | 401 ✓ |
| Correct secret | 200 | *(run with $ENGAGEFLOW_JOINER_SECRET)* |

## Phase 4–5: Sync + /api/profiles

See COOKIE_SYNC_PHASE4_5_PROOF.md. Run sync with secret, then verify has_cookie_json.

---

## Rollback Plan

If redeploy breaks EngageFlow:
1. `git revert` the push (or force-push previous origin/dev)
2. Redeploy EngageFlow from that revision
3. Remove ENGAGEFLOW_JOINER_SECRET from both services (disables cookie sync)

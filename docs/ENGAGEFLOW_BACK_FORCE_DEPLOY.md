# Force EngageFlow back to deploy aead079 / 48ff817

## 1) Confirmed: aead079 (and 48ff817) on origin/dev

```bash
git fetch origin
git log --oneline -n 5 origin/dev
```

**Result:** `origin/dev` now has:
- **48ff817** chore: force engageflow back rebuild after aead079
- **aead079** Joiner cookie sync: match by LOWER(TRIM(email)), dedupe profiles; EngageFlow GET /internal/joiner/profiles-cookies and /internal/joiner/debug-profiles
- a7e6205, c219091, ...

So the sync-fix commit **aead079** and the no-op **48ff817** are on `origin/dev`.

## 2) No-op commit pushed

- `git commit --allow-empty -m "chore: force engageflow back rebuild after aead079"`
- `git push origin dev --force` → **48ff817** is now the tip of `origin/dev`.

## 3) Redeploy triggered via API

- `serviceInstanceRedeploy` was called for engageflow back.
- After ~4 min polling, the service was still returning **c219091** and `/internal/joiner/debug-profiles` was still **404**.

## 4) If Railway still serves c219091

Do this in **Railway UI**:

1. **engageflow back** → **Settings** → **Source**
   - Repo: **limdin25/engageflow**
   - Branch: **dev**
   - Root: **backend**
   - Build: **Dockerfile**
   - **Save**

2. **engageflow back** → **Deployments** → **Redeploy**
   - Turn **“Disable build cache”** **ON** (if the option exists).
   - Confirm redeploy.

3. Wait for the new deployment to finish (build can take 5–10 min). Then run the proof below.

## Proof (after deploy shows SHA >= aead079)

```bash
# 1) SHA
curl -i https://engageflow-dev-ec26.up.railway.app/health | grep -i x-engageflow-git-sha
# Must be aead079... or 48ff817...

# 2) debug-profiles (set ENGAGEFLOW_JOINER_SECRET first)
curl -sS -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://engageflow-dev-ec26.up.railway.app/internal/joiner/debug-profiles | jq .
# Must return 3 rows, cookie_json_length > 0.

# 3) Sync
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://joiner-dev-abdb.up.railway.app/internal/joiner/sync-cookies | jq .
# Expect: updated: 3

# 4) Final profiles
curl -sS https://joiner-dev-abdb.up.railway.app/api/profiles | jq '.[] | {email, has_cookie_json, auth_status}'
# Expect: has_cookie_json true, auth_status connected for cookie accounts.
```

## Summary

- **aead079** and **48ff817** are on **origin/dev**.
- Redeploy was triggered via API; service was still on **c219091** after 4 min.
- Next step: in Railway UI, confirm Source (repo/branch/root), Save, then **Redeploy with “Disable build cache” ON**, wait for build to finish, then run the 4 proof commands above.

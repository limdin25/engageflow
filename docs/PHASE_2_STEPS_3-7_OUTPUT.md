# PHASE 2 — STEPS 3–7 RAILWAY RESTORE + PROOFS (OUTPUT)

**URLs:**
- ENGAGEFLOW_NEW_URL=https://engageflow-dev-ec26.up.railway.app
- JOINER_NEW_URL=https://joiner-dev.up.railway.app
- FRONTEND_NEW_URL=https://engageflow-front-dev.up.railway.app

**VPS archive:** `root@38.242.229.161:/root/engageflow_db_vps.tar.gz` (DB: `engageflow.db`)

---

## Step 3 — Railway backup (pre-overwrite)

**Attempted:** `GET /internal/backup-db` with `X-JOINER-SECRET`.

**Result:** **404 Not Found** — backup/restore endpoints are in backend commit `a3077f9` / `dbb59c2`. The currently live engageflow back image is from commit **db35b1f**, so these routes are not deployed yet.

**Backup ls (when endpoint is available after deploy):**
```bash
# After Railway deploys latest dev (dbb59c2), run:
curl -sS -o /tmp/railway_engageflow_db_backup.tar.gz \
  -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  "$ENGAGEFLOW_NEW_URL/internal/backup-db"
ls -la /tmp/railway_engageflow_db_backup.tar.gz
```
**Paste here when run:** _(No prior DB or ls output)_

**Unblock:** In Railway dashboard → **engageflow back** → **Deploy** → trigger **Redeploy** so it builds from latest **dev** (commit dbb59c2). Then re-run backup and Step 4.

---

## Step 4 — Restore VPS DB into /data

**Attempted:** `POST /internal/restore-db` with body `{"url":"http://38.242.229.161:8888/engageflow_db_vps.tar.gz"}`.

**Result:** **404 Not Found** (same cause: restore endpoint not in current deploy).

**VPS HTTP server:** A one-off Python HTTP server was started on the VPS so the archive is at `http://38.242.229.161:8888/engageflow_db_vps.tar.gz`. Stop it after restore: on VPS `pkill -f "python3 -m http.server 8888"` or restart the box.

**After deploy from latest dev, run:**
```bash
curl -sS -X POST "$ENGAGEFLOW_NEW_URL/internal/restore-db" \
  -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"url":"http://38.242.229.161:8888/engageflow_db_vps.tar.gz"}' | jq .
```
**Expected:** `{"ok":true,"integrity_check":"ok","db_path":"/data/engageflow.db","size_bytes":...}`

**Paste here when run:** _(restored ls + integrity_check from response)_

---

## Step 5 — Redeploy + dbinfo proof

**Current (pre-restore):**
```json
{"error":"no such column: cookie_json"}
```
*(Backend has no `cookie_json` column in current /data DB; migration and restore will fix.)*

**After restore + redeploy (latest backend with cookie_json migration), run:**
```bash
curl -sS $ENGAGEFLOW_NEW_URL/debug/dbinfo | jq .
```
**Expected:** `db_path` = `/data/engageflow.db`, `profiles_count` > 0, `profiles_with_cookie_json` ≥ 0, `file_size_bytes` ≈ 690757.

**Paste full JSON here:** _(after restore)_

---

## Step 6 — Joiner cookie sync

**Attempted:** `POST $JOINER_NEW_URL/internal/joiner/sync-cookies` with `X-JOINER-SECRET`.

**Result:** Joiner returned `Cannot POST /internal/joiner/sync-cookies` — deployed Joiner may be an older build. Repo has the route at `joiner/backend/server.js`.

**After Joiner is deployed from latest dev:**
```bash
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  "$JOINER_NEW_URL/internal/joiner/sync-cookies" | jq .
```
**Expected:** `{ "success": true, "scanned": N, "updated": M }`

**Paste JSON here:** _(after deploy + run)_

---

## Step 7 — Joiner profiles proof (no cookie content)

**Current output (safe fields only):**
```json
{"email":"hugords100+1@gmail.com","has_cookie_json":true,"auth_status":"connected"}
{"email":"hugords100@gmail.com","has_cookie_json":true,"auth_status":"connected"}
{"email":"marknoah2024@gmail.com","has_cookie_json":false,"auth_status":"disconnected"}
```

**Command:**
```bash
curl -sS $JOINER_NEW_URL/api/profiles | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'
```

After restore + sync-cookies, accounts that had cookies on VPS should show `has_cookie_json: true` and appropriate `auth_status`.

---

## Summary

| Step | Status | Blocker |
|------|--------|---------|
| 3 Backup | 404 | Deploy backend from latest dev (dbb59c2) |
| 4 Restore | 404 | Same |
| 5 dbinfo | Error (no cookie_json) | Restore DB + backend with migration |
| 6 sync-cookies | Cannot POST | Deploy Joiner from latest dev |
| 7 profiles | OK | — |

**Next actions:**
1. In Railway, redeploy **engageflow back** from latest **dev** so backup/restore endpoints and cookie_json migration are live.
2. Run Step 3 (backup), then Step 4 (restore) with the VPS URL. If the VPS HTTP server stopped, start it again: on VPS `cd /root && python3 -m http.server 8888 &`.
3. Redeploy **engageflow back** once more after restore (optional, to clear any in-memory state).
4. Run Step 5 (dbinfo) and paste JSON.
5. Redeploy **joiner-old** (Joiner) from latest dev, then run Step 6 (sync-cookies).
6. Run Step 7 again and paste the profiles table.
7. **Cleanup:** Remove `ENGAGEFLOW_DEBUG=1` from engageflow back and Joiner, redeploy both.

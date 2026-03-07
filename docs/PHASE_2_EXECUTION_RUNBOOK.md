# PHASE 2 — VPS → RAILWAY FULL MIRROR (EXECUTION RUNBOOK)

**Role:** Lead DevOps/SRE. Hugo does not click. Execute via API/CLI.  
**Doc to follow:** `docs/PHASE_2_RAILWAY_RESTORE.md` (canonical).

**Non‑negotiables:** No deletes of -old services/volumes. No printing cookie_json. Stop on any proof failure. All outputs copy‑pasteable.

---

## PART 1 — SELF CHECKLIST (COMPLETED)

### A) Phase 0–1 pipeline

| Check | Result |
|-------|--------|
| **GitHub** repo `limdin25/engageflow`, branch `dev` | OK |
| **HEAD SHA** (expected 16f7e68 or newer) | `db35b1f` (newer) |
| **Recent commits** | db35b1f, 61d9964, b8bb430, 16f7e68, 3084e78 |

**Note:** `engageflow-new`, `frontend-new`, `joiner-new` have **no DEV service instances** (no domains in DEV). Phase 2 target services are the **running DEV services** with domains:

| Logical role | Railway service name | Service ID | DEV URL |
|--------------|----------------------|------------|---------|
| **ENGAGEFLOW_NEW_URL** (backend) | engageflow back | e52345be-0feb-4798-9cb1-2efd46d349e9 | https://engageflow-dev-ec26.up.railway.app |
| **FRONTEND_NEW_URL** | engageflow front | f496b459-eb64-4116-9ca2-f0621a3136ba | https://engageflow-front-dev.up.railway.app |
| **JOINER_NEW_URL** | joiner-old | 50e311ec-ab40-4467-85c2-989b009b1829 | https://joiner-dev.up.railway.app |

**Service identity checks (done):**

- EngageFlow back: `curl -sS $ENGAGEFLOW_NEW_URL/health` → `{"status":"ok","running":false}`
- Joiner: `curl -sS $JOINER_NEW_URL/` → `{"status":"ok","service":"joiner",...}`
- Frontend: serves HTML (200)

### B) Secrets and env (names only)

- **engageflow back:** `ENGAGEFLOW_DB_PATH` (= `/data/engageflow.db`), `OPENAI_API_KEY`, `ENGAGEFLOW_JOINER_SECRET`, `ENGAGEFLOW_DEBUG` (= `1` during proof).
- **joiner-old:** `ENGAGEFLOW_JOINER_SECRET`, `ENGAGEFLOW_INTERNAL_URL` (= `https://engageflow-dev-ec26.up.railway.app`).

### C) VPS DB liveness

- **Not run from this environment:** SSH to VPS (72.61.147.80) failed (Permission denied, no key). **You must run Step 1 on the VPS** and optionally upload the archive to a private URL or make it available for Step 4.

### D) Rollback readiness

- engageflow-old, joiner-old, frontend-old exist (not deleted).
- **Before overwriting `/data/engageflow.db`:** run Step 3 (backup current Railway DB) and keep the backup.

---

## PART 2 — IMPLEMENTATION STATUS

### Step 1 — VPS snapshot (YOU RUN ON VPS)

**On VPS** (e.g. `ssh root@72.61.147.80`):

```bash
sqlite3 /root/engageflow-shared/engageflow.db "PRAGMA checkpoint(TRUNCATE);"
sqlite3 /root/engageflow-shared/engageflow.db "PRAGMA integrity_check;"
# Expect: ok

cd /root/engageflow-shared
tar -czf /root/engageflow_db_vps.tar.gz engageflow.db
du -sh /root/engageflow_db_vps.tar.gz
```

**Proof to paste:** integrity_check output + archive size.

---

### Step 2 — Attach volume to backend (DONE VIA API)

- **Volume created** on service **engageflow back** (DEV): mount `/data`, volume id `7c038710-bc5f-4fcc-a4ec-264275b5effb`.
- **Variables set:** `ENGAGEFLOW_DB_PATH=/data/engageflow.db`, `ENGAGEFLOW_DEBUG=1`.
- **Redeploy** triggered for engageflow back.

**Proof:** In Railway dashboard → engageflow back → Variables: `ENGAGEFLOW_DB_PATH` present; Volumes: one volume at `/data`.

---

### Step 3 — Backup current Railway DB (BEFORE RESTORE)

You need a **one-off job** that has the **same** volume as engageflow back mounted at `/data`. Options:

- Railway “Run” / job that mounts the volume and runs a shell, or
- Temporary deploy that runs once: backup then exits.

**Inside that job:**

```bash
cd /data
tar -czf /tmp/railway_engageflow_db_backup.tar.gz engageflow.db* 2>/dev/null || true
ls -la /tmp/railway_engageflow_db_backup.tar.gz 2>/dev/null || echo "No prior DB (empty volume)"
```

**Proof to paste:** `ls -la` of backup file or “No prior DB”.

---

### Step 4 — Restore VPS DB into `/data`

In the **same** one-off job (or a job that has the archive and the volume):

- Put the VPS archive at `/tmp/engageflow_db_vps.tar.gz` (e.g. scp from VPS, or download from a private URL; **do not commit to git**).
- Then:

```bash
cd /data
tar -xzf /tmp/engageflow_db_vps.tar.gz
ls -la /data/engageflow.db
sqlite3 /data/engageflow.db "PRAGMA integrity_check;"
# Expect: ok
```

**Proof to paste:** `ls -la /data/engageflow.db` (size, timestamp) + integrity_check output.

---

### Step 5 — Prove EngageFlow is using restored DB

After restore, **redeploy** engageflow back once (so it sees the new file). Then:

```bash
export ENGAGEFLOW_NEW_URL="https://engageflow-dev-ec26.up.railway.app"
curl -sS "$ENGAGEFLOW_NEW_URL/debug/dbinfo" | jq .
```

**Expected:** `db_path` == `/data/engageflow.db`, `profiles_count` > 0, `profiles_with_cookie_json` >= 0, `file_size_bytes` ~ restored size.

If you see `"error": "no such column: cookie_json"`, the backend was updated to add that column in `ensure_tables()`; redeploy engageflow back and retry. A **restored VPS DB** usually already has `cookie_json`.

**Paste full JSON (no cookie contents).**

---

### Step 6 — Joiner cookie hydration (Option 2)

Ensure `ENGAGEFLOW_JOINER_SECRET` is the same on engageflow back and joiner-old. Then:

```bash
export JOINER_NEW_URL="https://joiner-dev.up.railway.app"
# Set secret (do not paste in logs)
export ENGAGEFLOW_JOINER_SECRET="<your-secret>"

curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  "$JOINER_NEW_URL/internal/joiner/sync-cookies" | jq .
```

**Expected:** `{ "success": true, "scanned": N, "updated": M }`.  
**Paste output (no cookie contents).**

---

### Step 7 — Prove Joiner sees cookies (no cookie content in output)

```bash
curl -sS "$JOINER_NEW_URL/api/profiles" | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json != null)), auth_status}'
```

**Paste output.** Expected: accounts that had cookies on VPS show `has_cookie_json: true` and appropriate `auth_status`.

---

### Step 8 — UI confirmation (Hugo verifies)

- **frontend-new URL:** https://engageflow-front-dev.up.railway.app  
- Dashboard: profiles and activity history present.  
- Joiner (https://joiner-dev.up.railway.app): Accounts tab shows Connected where expected, without clicking Test Auth.

---

### Step 9 — Cleanup

Remove `ENGAGEFLOW_DEBUG=1` from engageflow back and (if set) from joiner-old. Redeploy both.

---

## ROLLBACK (if any failure)

- Do **not** touch VPS.
- Restore `/data` from `/tmp/railway_engageflow_db_backup.tar.gz` (extract in same one-off job), then redeploy engageflow back.
- If needed, point traffic back to engageflow-old / frontend-old / joiner-old.

---

## FINAL OUTPUT CHECKLIST

1. **URLs:** ENGAGEFLOW_NEW_URL=https://engageflow-dev-ec26.up.railway.app, FRONTEND_NEW_URL=https://engageflow-front-dev.up.railway.app, JOINER_NEW_URL=https://joiner-dev.up.railway.app  
2. **VPS:** integrity_check result + archive size (from Step 1 on VPS).  
3. **Railway pre-backup:** ls of backup file or “No prior DB”.  
4. **Railway restored:** ls -la engageflow.db + integrity_check.  
5. **EngageFlow /debug/dbinfo:** full JSON.  
6. **Joiner sync-cookies:** full JSON.  
7. **Joiner /api/profiles:** table from jq (email, has_cookie_json, auth_status only).  
8. **Cleanup:** ENGAGEFLOW_DEBUG removed; redeploy confirmed.

# PHASE 2 — VPS → RAILWAY FULL STATE RESTORE (DB + COOKIES + HISTORY)

## Goal

Make Railway match VPS state: profiles, cookies, activity, history, everything.  
**Do NOT "start fresh".** Restore the VPS SQLite as the source of truth.

## Non-negotiables

- **Do not print cookie contents.**
- **Do not delete old Railway services/volumes** (keep rollback).
- **Stop if any proof fails.**

---

## Target services (new)

Fill these from **Railway dashboard** → each service → **Settings → Domains** (or **Generate Domain**). Use the **-new** services (Phase 0–1), not -old.

| Service            | URL (fill after deploy) |
|--------------------|-------------------------|
| **engageflow-new** | `<FILL>` e.g. `https://engageflow-new-xxx.up.railway.app` |
| **joiner-new**     | `<FILL>` e.g. `https://joiner-new-xxx.up.railway.app` |
| **frontend-new**   | `<FILL>` e.g. `https://frontend-new-xxx.up.railway.app` |

---

## Step 1 — VPS DB snapshot (source of truth)

**On VPS** (e.g. `ssh root@72.61.147.80` or your VPS host):

```bash
# 1) Checkpoint to fold WAL
sqlite3 /root/engageflow-shared/engageflow.db "PRAGMA checkpoint(TRUNCATE);"

# 2) Integrity check
sqlite3 /root/engageflow-shared/engageflow.db "PRAGMA integrity_check;"
# Expect: ok

# 3) Archive DB only
cd /root/engageflow-shared
tar -czf /root/engageflow_db_vps.tar.gz engageflow.db
du -sh /root/engageflow_db_vps.tar.gz
```

**Record:** VPS DB archive size and `integrity_check` result → **[Output 1]** below.

---

## Step 2 — Attach Railway volume to engageflow-new (only)

In **Railway UI**:

1. Open **engageflow-new** → **Settings** (or **Variables**).
2. **Volumes** → **Add Volume** → mount path: **`/data`**.
3. Set variable: **`ENGAGEFLOW_DB_PATH`** = **`/data/engageflow.db`**.
4. **Redeploy** engageflow-new.

Do **not** attach a volume to joiner-new or frontend-new for this phase.

---

## Step 3 — Restore DB into engageflow-new volume

Run a **one-off restore** that has access to the **same** volume as engageflow-new at `/data`.

**Option A — Railway one-off run (if supported)**  
Use a job/run that mounts the same volume and runs:

```bash
# Assume archive is in /tmp (e.g. uploaded or downloaded to a secure location)
cd /data
tar -xzf /tmp/engageflow_db_vps.tar.gz
ls -la /data/engageflow.db
sqlite3 /data/engageflow.db "PRAGMA integrity_check;"
# Expect: ok
```

**Option B — Copy from VPS to a temp location, then into volume**  
If Railway doesn’t support one-off jobs with volume mount, you may need to:

- Download the archive from VPS to your machine (e.g. `scp root@vps:/root/engageflow_db_vps.tar.gz .`).
- Use Railway’s volume restore/import flow if available, or a custom deploy that writes the extracted DB to `/data` once (then remove that code and redeploy normal app).

**Record:** `ls -la /data/engageflow.db` and `integrity_check` result after restore → **[Output 2]**.

---

## Step 4 — Proof EngageFlow is using restored DB

1. **Redeploy** engageflow-new backend after the restore (so it picks up the file on `/data`).
2. Set **`ENGAGEFLOW_DEBUG=1`** on engageflow-new (required for `/debug/dbinfo`).
3. Run:

```bash
curl -sS "<ENGAGEFLOW_NEW_URL>/debug/dbinfo" | jq
```

**Confirm:**

- `db_path` == `/data/engageflow.db`
- `profiles_count` > 0
- `profiles_with_cookie_json` >= 0 (and > 0 if VPS had cookies)
- `file_size_bytes` in the same ballpark as the restored file

**Record:** Full JSON output → **[Output 3]**.

---

## Step 5 — Joiner cookie hydration (Option 2)

1. **Both** engageflow-new and joiner-new must have **`ENGAGEFLOW_JOINER_SECRET`** set to the **same** value.
2. On **joiner-new** set: **`ENGAGEFLOW_INTERNAL_URL`** = **`<ENGAGEFLOW_NEW_URL>`** (no trailing slash).

Then run:

```bash
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  "<JOINER_NEW_URL>/internal/joiner/sync-cookies" | jq
```

**Expect:** `scanned` >= `profiles_count`, `updated` >= 1 (if any profile had cookies in the restored DB).

**Record:** Full JSON output → **[Output 4]**.

---

## Step 6 — Proof Joiner sees cookies

```bash
curl -sS "<JOINER_NEW_URL>/api/profiles" | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'
```

**Expect:** Accounts that had cookies on VPS show `has_cookie_json: true` and appropriate `auth_status` (e.g. connected).

**Record:** Table or snippet → **[Output 5]**.

---

## Step 7 — UI proof

Open **frontend-new** dashboard (URL from table above):

- [ ] **Profiles** are populated (same as VPS).
- [ ] **Activity** timeline has historical entries.
- [ ] **Joiner** (if you open Joiner URL) → **Accounts** tab shows **Connected** for cookie accounts without clicking Test Auth.

**Record:** Pass/fail per item → **[Output 6]**.

---

## Rollback plan (if any failure)

- **Do NOT** touch the VPS.
- **Option A:** Restore the engageflow-new volume from a backup (e.g. take a copy of the Railway DB **before** overwriting with VPS archive, then re-extract that copy into `/data`).
- **Option B:** Detach the `/data` volume from engageflow-new and redeploy so the service runs with an empty/Ephemeral state again.

---

## Output required (checklist)

Fill after each step:

1. **[Output 1]** VPS DB size + `integrity_check` result  
   - `du -sh /root/engageflow_db_vps.tar.gz`: _____________  
   - `PRAGMA integrity_check`: _____________

2. **[Output 2]** Railway restore confirmation  
   - `ls -la /data/engageflow.db`: _____________  
   - `PRAGMA integrity_check` (on Railway volume): _____________

3. **[Output 3]** `/debug/dbinfo` after restore (paste JSON or key fields)  
   - `db_path`: _____________  
   - `profiles_count`: _____________  
   - `profiles_with_cookie_json`: _____________  
   - `file_size_bytes`: _____________

4. **[Output 4]** sync-cookies response (paste JSON or key fields)  
   - `scanned`: _____________  
   - `updated`: _____________

5. **[Output 5]** `/api/profiles` cookie booleans (table or summary)  
   - _____________

6. **[Output 6]** UI checklist  
   - Profiles populated: Pass / Fail  
   - Activity history: Pass / Fail  
   - Joiner Connected: Pass / Fail  

---

## Notes

- **`/debug/dbinfo`** is only available when **`ENGAGEFLOW_DEBUG=1`** is set on the engageflow-new service; otherwise it returns 404.
- **Cookie contents** must never be logged or printed; backend and Joiner already avoid that.
- Phase 0–1 must be done first (new services deployed, repo connected, no volume on engageflow-new until this phase).

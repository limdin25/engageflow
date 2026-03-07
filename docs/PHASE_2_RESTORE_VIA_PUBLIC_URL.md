# Phase 2 — Restore via public URL (Railway can’t reach VPS)

## What happened

- **Restore was run** on engageflow back with `url: http://38.242.229.161:8888/engageflow_db_vps.tar.gz`.
- **Result:** Railway backend **cannot connect to the VPS** (connection timeout). So restore failed with:
  - `Download failed: ... Connection to 38.242.229.161 timed out (connect timeout=120)`.

So **Railway → VPS** is not usable for the restore URL. Use a **public HTTPS URL** that Railway can reach instead.

## Security rule (see PHASE_2_RESTORE_SECURE_HTTPS.md)

The tarball contains **DB + cookies**. Do **not** use Gist, GitHub, or any **permanent** public link. Use an **expiring presigned URL** (S3/R2, 5–15 min TTL). Full steps: **docs/PHASE_2_RESTORE_SECURE_HTTPS.md**.

## What you need

1. **ENGAGEFLOW_JOINER_SECRET** — same value on **engageflow back** and **joiner-dev-abdb** (already aligned via API).
2. **ENGAGEFLOW_DEBUG=1** on engageflow back (already set).
3. **Tarball URL** — **presigned HTTPS only** (S3/R2, short TTL). Do not paste the URL in chat; set `RESTORE_URL` in env.

## Steps

### 1. Get the tarball to a presigned HTTPS URL (no permanent links)

See **docs/PHASE_2_RESTORE_SECURE_HTTPS.md** for: `scp` from VPS, upload to S3/R2, generate presigned URL (5–15 min TTL), set `RESTORE_URL` in env. Do **not** use Gist or GitHub.

### 2. Run restore (from your machine)

```bash
# RESTORE_URL and ENGAGEFLOW_JOINER_SECRET must be set in env (do not paste in chat)
curl -sS -X POST -H "Content-Type: application/json" \
  -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  -d "{\"url\":\"$RESTORE_URL\"}" \
  https://engageflow-dev-ec26.up.railway.app/internal/restore-db | jq .
```

Or run the full flow: `./scripts/phase-2-restore-secure.sh` (uses `RESTORE_URL` and `ENGAGEFLOW_JOINER_SECRET` from env).

- If the backend is still the **synchronous** version: you get either **200** with `ok: true` and `integrity_check`, or **502** if the download fails.
- If the **async** version is deployed (commit a7e6205): you get **202** with `"status": "accepted"`; then poll dbinfo until `profiles_count` > 0.

### 3. Proofs (run after restore succeeds)

**A) dbinfo**

```bash
curl -sS https://engageflow-dev-ec26.up.railway.app/debug/dbinfo | jq .
```

Expect: `profiles_count` > 0, `file_size_bytes` larger than 139264 (close to VPS DB size).

**B) sync-cookies**

```bash
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://joiner-dev-abdb.up.railway.app/internal/joiner/sync-cookies | jq .
```

Expect: `updated` > 0 if the restored DB has cookie_json.

**C) profiles**

```bash
curl -sS https://joiner-dev-abdb.up.railway.app/api/profiles | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'
```

Expect: `has_cookie_json: true` for accounts that have cookies in the restored DB.

---

## Backend change (already in repo)

Commit **a7e6205** makes `POST /internal/restore-db` return **202 Accepted** and run the download in a background thread, so Railway’s gateway won’t time out. After that deploy, restore with a **working public URL** will return 202 and the DB will be restored asynchronously; poll `/debug/dbinfo` until `profiles_count` > 0.

The **blocker** right now is only that the **URL must be reachable from Railway** (e.g. public HTTPS). The VPS URL is not reachable (connection timeout).

---

## Output required (paste all after a successful restore)

Once restore succeeds (using a public URL), paste:

**1. Restore response JSON**  
(200 with `ok: true, integrity_check, db_path, size_bytes` — or 202 with `status: "accepted"` if async is deployed.)

**2. dbinfo JSON (after restore)**  
Expect: `profiles_count` > 0, `file_size_bytes` > 139264.

**3. Sync JSON (after restore)**  
Expect: `updated` > 0 if VPS DB had cookies.

**4. Profiles table (after restore)**  
Expect: `has_cookie_json: true` for cookie accounts.

### Current outputs (restore not applied — Railway could not reach VPS)

| Item | Output |
|------|--------|
| **Restore response** | `{"success":false,"error":"request_error","message":"Download failed: ... Connection to 38.242.229.161 timed out ..."}` |
| **dbinfo** | `{"db_path":"/data/engageflow.db","file_size_bytes":139264,"profiles_count":0,"profiles_with_cookie_json":0}` |
| **sync** | `{"success":true,"scanned":4,"updated":0}` |
| **profiles** | 4 profiles, all `has_cookie_json: false`, `auth_status: "disconnected"` |

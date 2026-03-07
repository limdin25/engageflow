# PHASE 2 — FINAL OUTPUT (EXECUTED BY AGENT)

## Endpoint security (confirmed before execution)

- **Backup/restore:** Both require `_require_internal_restore_auth(request)`:
  - `ENGAGEFLOW_DEBUG=1` (otherwise 404).
  - `X-JOINER-SECRET` header matching env (otherwise 401).
- No DB bytes or `cookie_json` logged; responses are file download (backup) or `{ok, integrity_check, db_path, size_bytes}` (restore).

---

## Deployed SHAs

- **engageflow back** (https://engageflow-dev-ec26.up.railway.app): **db35b1f** (from `curl -i /health` → `X-EngageFlow-Git-Sha`). Backend has not yet deployed **dbb59c2** / **c219091** (backup/restore endpoints).
- **Joiner** (https://joiner-dev.up.railway.app): current deploy does not expose `POST /internal/joiner/sync-cookies` (returns Cannot POST).

---

## 1) Health

```
HTTP/2 200
x-engageflow-git-sha: db35b1f99a4393919379a80d657021eb39afffed
{"status":"ok","running":false}
```

---

## 2) Backup

- **Response:** `404 Not Found` (endpoint not in deployed image db35b1f).
- **Backup file:** Request wrote 22-byte JSON error body to `/tmp/railway_backup_phase2.tar.gz` (not a tarball). No container ls (endpoint not reached).

---

## 3) Restore

- **Response:** `{"detail":"Not Found"}` (restore endpoint not in deployed image).

---

## 4) dbinfo

```json
{"error":"no such column: cookie_json"}
```

---

## 5) sync-cookies

- **Response:** `Cannot POST /internal/joiner/sync-cookies` (HTML from Joiner; route not in deployed Joiner image).

---

## 6) Profiles table (no cookie content)

```json
{"email":"hugords100+1@gmail.com","has_cookie_json":true,"auth_status":"connected"}
{"email":"hugords100@gmail.com","has_cookie_json":true,"auth_status":"connected"}
{"email":"marknoah2024@gmail.com","has_cookie_json":false,"auth_status":"disconnected"}
```

---

## 7) Cleanup (done)

- **ENGAGEFLOW_DEBUG** set to **0** on engageflow back and on Joiner (variableUpsert).
- **Redeploy** triggered for both services.

---

## Blocker summary

Railway is serving **engageflow back** from commit **db35b1f**. Commits **dbb59c2** and **c219091** (backup/restore + cookie_json migration) are on `dev` but have not been built/deployed for this service (redeploys and `railway up` did not switch the live image to latest dev). Until the backend runs an image that includes those commits, backup/restore and dbinfo (with cookie_json) cannot be used. Joiner deploy does not include the sync-cookies route.

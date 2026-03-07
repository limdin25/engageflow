# Phase 2 Continue — Secret fix + restore + proofs

## Step 1 — Secret alignment ✅

- **ENGAGEFLOW_JOINER_SECRET** was copied from **joiner** (joiner-dev-abdb, service `f4b6e971`) to **engageflow back** (service `e52345be`) via Railway GraphQL API.
- **engageflow back** was redeployed to pick up the variable.

## Step 1 proof — backup-db ✅

```bash
curl -i -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://engageflow-dev-ec26.up.railway.app/internal/backup-db
```

**Result: HTTP/2 200** (with `content-disposition: attachment; filename="railway_engageflow_db_backup.tar.gz"`, `x-engageflow-git-sha: c21909188e98afccb124c4d99ca6a3d102b74335`).

---

## Step 2 — Restore DB (run manually if restore hung)

Restore was triggered but may hang if Railway cannot reach the VPS or the VPS HTTP server is down. **On the VPS** ensure the file is served:

```bash
# On VPS 38.242.229.161
cd /root && python3 -m http.server 8888 &
# or: serve the file only, e.g. from /root where engageflow_db_vps.tar.gz lives
```

Then **from your machine** (set `ENGAGEFLOW_JOINER_SECRET` to the same value as in Railway for **joiner**):

```bash
# Restore
curl -sS -X POST -H "Content-Type: application/json" \
  -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  -d '{"url":"http://38.242.229.161:8888/engageflow_db_vps.tar.gz"}' \
  https://engageflow-dev-ec26.up.railway.app/internal/restore-db | jq .
```

Paste the **restore response JSON** below.

---

## Step 3 — dbinfo

```bash
curl -sS https://engageflow-dev-ec26.up.railway.app/debug/dbinfo | jq .
```

**Expected:** `profiles_count` > 0, `db_path` = `/data/engageflow.db`, no `cookie_json` column error.

Paste the **dbinfo JSON** below.

---

## Step 4 — Sync cookies (joiner-dev-abdb only)

Use **only** `https://joiner-dev-abdb.up.railway.app`:

```bash
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://joiner-dev-abdb.up.railway.app/internal/joiner/sync-cookies | jq .
```

Paste the **sync JSON** below.

---

## Step 5 — Profiles table

```bash
curl -sS https://joiner-dev-abdb.up.railway.app/api/profiles | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'
```

Paste the **profiles** output below.

---

## Output checklist

| Item            | Status | Your output |
|-----------------|--------|-------------|
| backup-db 200   | ✅     | Confirmed above |
| restore JSON    | ⏳     | _Restore was not applied — see below_ |
| dbinfo JSON     | ✅     | See below (pre-restore: profiles_count 0) |
| sync-cookies JSON | ✅   | See below |
| profiles        | ✅     | See below |

### Current outputs (restore not yet applied)

**dbinfo** (engageflow back — DB not yet restored from VPS):
```json
{
  "db_path": "/data/engageflow.db",
  "file_size_bytes": 139264,
  "profiles_count": 0,
  "profiles_with_cookie_json": 0
}
```

**sync-cookies** (joiner-dev-abdb):
```json
{ "success": true, "scanned": 4, "updated": 0 }
```

**profiles** (joiner-dev-abdb):
- hugords100+1@gmail.com — has_cookie_json: false, auth_status: disconnected  
- hugords100@gmail.com — has_cookie_json: false, auth_status: disconnected  
- marknoah2024@gmail.com (×2) — has_cookie_json: false, auth_status: disconnected  

**Next:** Run restore (Step 2 above) with the VPS HTTP server serving `engageflow_db_vps.tar.gz`, then re-run dbinfo (expect `profiles_count` > 0), sync-cookies, and profiles.

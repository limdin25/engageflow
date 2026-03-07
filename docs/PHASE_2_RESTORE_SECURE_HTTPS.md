# Phase 2 restore — public HTTPS only, no leaks

## Security rule

The tarball contains **DB + cookies**. Do **not** upload to Gist, GitHub, or any **permanent** public link.

- Use an **expiring, private** link: **S3 or R2 presigned URL**, TTL **5–15 minutes**.
- If you use another file host, it must have **immediate expiry** and **no indexing**.
- **Do not paste** the presigned URL or `ENGAGEFLOW_JOINER_SECRET` in chat or logs. Store in env only.

---

## Step 1 — Create HTTPS link (you run this locally)

### 1.1 Get the tarball from the VPS

```bash
scp root@38.242.229.161:/root/engageflow_db_vps.tar.gz .
```

### 1.2 Upload to S3 or R2 and generate a presigned URL (short TTL)

**Option A — AWS S3**

```bash
# Set your bucket and key (use a one-off key, e.g. restore-$(date +%s).tar.gz)
BUCKET=your-bucket
KEY=restore-$(date +%s).tar.gz
aws s3 cp engageflow_db_vps.tar.gz "s3://${BUCKET}/${KEY}"

# Presigned GET URL, 15 min expiry. Store in env; do not paste in chat.
export RESTORE_URL=$(aws s3 presign "s3://${BUCKET}/${KEY}" --expires-in 900)
# Optional: delete object after restore (schedule or run manually)
# aws s3 rm "s3://${BUCKET}/${KEY}"
```

**Option B — Cloudflare R2 (S3-compatible)**

```bash
# R2 endpoint and credentials in env (e.g. AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, endpoint URL)
# Presign with AWS CLI using --endpoint-url https://<account_id>.r2.cloudflarestorage.com
KEY=restore-$(date +%s).tar.gz
aws s3 cp engageflow_db_vps.tar.gz "s3://your-r2-bucket/${KEY}" --endpoint-url "https://<ACCOUNT_ID>.r2.cloudflarestorage.com"
export RESTORE_URL=$(aws s3 presign "s3://your-r2-bucket/${KEY}" --expires-in 900 --endpoint-url "https://<ACCOUNT_ID>.r2.cloudflarestorage.com")
```

### 1.3 Set the joiner secret (same as Railway → joiner-dev-abdb)

```bash
export ENGAGEFLOW_JOINER_SECRET='<value-from-railway-joiner-variables>'
```

Do **not** paste `RESTORE_URL` or `ENGAGEFLOW_JOINER_SECRET` anywhere.

---

## Step 2 — Trigger restore (EngageFlow)

```bash
curl -sS -X POST \
  -H "Content-Type: application/json" \
  -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  -d "{\"url\":\"$RESTORE_URL\"}" \
  https://engageflow-dev-ec26.up.railway.app/internal/restore-db | jq .
```

**Expect:** `202 Accepted` and body like `{"status":"accepted","message":"Restore started in background. Poll /debug/dbinfo for profiles_count."}`.

---

## Step 3 — Poll until restored

Repeat every ~5s until `profiles_count` > 0 and `file_size_bytes` > 139264:

```bash
curl -sS https://engageflow-dev-ec26.up.railway.app/debug/dbinfo | jq .
```

Or use the script (see below) which polls for you.

---

## Step 4 — Joiner sync + proof

```bash
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://joiner-dev-abdb.up.railway.app/internal/joiner/sync-cookies | jq .

curl -sS https://joiner-dev-abdb.up.railway.app/api/profiles | jq \
  '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'
```

---

## Outputs to paste (no secrets, no cookie contents)

Paste only these four:

1. **Restore JSON** — the 202 response body.
2. **dbinfo JSON** after restore — `profiles_count` > 0, `file_size_bytes` > 139264.
3. **Sync JSON** — `updated` > 0 if cookies existed in the DB.
4. **Profiles table** — the `jq` output from Step 4 (email, has_cookie_json, auth_status only).

---

## Script (Steps 2–4 only)

From repo root, with `RESTORE_URL` and `ENGAGEFLOW_JOINER_SECRET` already set:

```bash
./scripts/phase-2-restore-secure.sh
```

The script does not echo the URL or secret; it prints only the four outputs above.

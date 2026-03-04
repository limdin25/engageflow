# Option 2 Final Close — Get Cookies → Sync → Prove UI

## Changes Made

1. **EngageFlow:** Added `PUT /internal/joiner/profiles/{profile_id}/cookie` — accepts `{cookie_json}` and stores in EngageFlow DB. Secret-gated. Never logs cookie contents.

2. **Joiner:** Connect and paste-cookies now **push** cookies to EngageFlow after storing locally. So when you Connect in Joiner UI, cookies land in both Joiner DB and EngageFlow DB.

## Step-by-Step Proof

### Step 1: Confirm EngageFlow has no cookies (before Connect)

Profile IDs:
- hugords100: `d56f73d2-08bc-4412-a018-960fe89362ad`
- marknoah: `aa599316-f52c-4428-94df-4d101078c765`

```bash
# hugords100
curl -sS -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://engageflow-dev.up.railway.app/internal/joiner/profiles/d56f73d2-08bc-4412-a018-960fe89362ad/cookie \
  | jq 'if .cookie_json == null then "null" else "non-null" end'

# marknoah
curl -sS -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://engageflow-dev.up.railway.app/internal/joiner/profiles/aa599316-f52c-4428-94df-4d101078c765/cookie \
  | jq 'if .cookie_json == null then "null" else "non-null" end'
```

**Expected before Connect:** `"null"` for both.

### Step 2: Add cookies via Connect

1. Open **Communities → Join → Accounts** (Joiner UI).
2. For **hugords100**: Click **Connect**, enter Skool password, submit.
3. For **marknoah**: Click **Connect**, enter Skool password, submit.

After each Connect, cookies are stored in Joiner DB and pushed to EngageFlow.

**Verify after Connect:**
```bash
# hugords100
curl -sS -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://engageflow-dev.up.railway.app/internal/joiner/profiles/d56f73d2-08bc-4412-a018-960fe89362ad/cookie \
  | jq 'if .cookie_json == null then "null" else "non-null" end'

# marknoah
curl -sS -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://engageflow-dev.up.railway.app/internal/joiner/profiles/aa599316-f52c-4428-94df-4d101078c765/cookie \
  | jq 'if .cookie_json == null then "null" else "non-null" end'
```

**Expected after Connect:** `"non-null"` for both.

### Step 3: Run cookie sync

```bash
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://joiner-dev.up.railway.app/internal/joiner/sync-cookies | jq .
```

**Expected:** `{ success: true, scanned: 3, updated: 0 }` (updated 0 if Joiner already has cookies from Connect).

### Step 4: Verify Joiner /api/profiles

```bash
curl -sS https://joiner-dev.up.railway.app/api/profiles | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'
```

**Expected:**
- hugords100+1: `has_cookie_json: true`, `auth_status: "connected"`
- hugords100: `has_cookie_json: true`, `auth_status: "connected"`
- marknoah2024: `has_cookie_json: true`, `auth_status: "connected"`

### Step 5: UI proof

Hard refresh **Communities → Join → Accounts**. All 3 accounts should show **Connected** without clicking Test Auth.

### Step 6: Cleanup

Remove `ENGAGEFLOW_DEBUG=1` from both EngageFlow and Joiner in Railway. Redeploy.

# EngageFlow Option 1: Share EngageFlow DB Volume with Joiner

**Goal:** Railway Joiner and EngageFlow read the SAME SQLite database file, so `cookie_json` written anywhere is visible everywhere.

**Status:** Phase 1 (backend dbinfo) complete. Phase 2–5 require Railway dashboard changes and optional Joiner patch.

---

## Phase 1 — Evidence Before Change

### A) EngageFlow Service

**Endpoint:** `GET /debug/dbinfo` (requires `ENGAGEFLOW_DEBUG=1`)

```bash
# Set ENGAGEFLOW_DEBUG=1 on engageflow service, redeploy, then:
curl -sS "https://engageflow-dev.up.railway.app/debug/dbinfo" | jq
```

**Expected response:**
```json
{
  "db_path": "/data/engageflow.db",
  "file_size_bytes": 123456,
  "profiles_count": 3,
  "profiles_with_cookie_json": 1
}
```

### B) Joiner Service

**If Joiner has `/debug/dbinfo`** (add below if not present):

```bash
# Set ENGAGEFLOW_DEBUG=1 on joiner service, redeploy, then:
curl -sS "https://joiner-dev.up.railway.app/debug/dbinfo" | jq
```

**Joiner patch (add to joiner/backend/server.js):**

```javascript
// Add after app.get('/', ...) — gated by ENGAGEFLOW_DEBUG=1
if (process.env.ENGAGEFLOW_DEBUG === '1') {
  app.get('/debug/dbinfo', (req, res) => {
    try {
      const config = require('./config-loader');
      const path = require('path');
      const fs = require('fs');
      const dbPath = config.ENGAGEFLOW_DB_PATH;
      const size = fs.existsSync(dbPath) ? fs.statSync(dbPath).size : 0;
      let profilesCount = 0;
      let profilesWithCookieJson = 0;
      if (fs.existsSync(dbPath) && size > 0) {
        const r = engageflowDb.prepare('SELECT COUNT(*) as c FROM profiles').get();
        profilesCount = r?.c ?? 0;
        const r2 = engageflowDb.prepare(
          "SELECT COUNT(*) as c FROM profiles WHERE cookie_json IS NOT NULL AND length(trim(COALESCE(cookie_json,''))) > 0"
        ).get();
        profilesWithCookieJson = r2?.c ?? 0;
      }
      res.json({
        db_path: dbPath,
        file_size_bytes: size,
        profiles_count: profilesCount,
        profiles_with_cookie_json: profilesWithCookieJson,
      });
    } catch (e) {
      res.status(500).json({ error: String(e.message) });
    }
  });
}
```

### Phase 1 Evidence Table (fill after running)

| Service | DB path | file_size_bytes | profiles_count | profiles_with_cookie_json |
|---------|---------|-----------------|----------------|---------------------------|
| EngageFlow | | | | |
| Joiner | | | | |

**Before change:** EngageFlow DB should have cookies from Connect/Paste. Joiner DB (separate volume) typically has `profiles_with_cookie_json` lower or 0 due to API sync omitting `cookie_json`.

---

## Phase 2 — Railway Config Change (NO CODE)

### Prerequisites

1. Railway supports **multiple services attaching the same volume**.
2. EngageFlow volume name and mount path (e.g. `/data`).

### Steps

1. **In Railway Dashboard → EngageFlow service:**
   - Note the volume name (e.g. `engageflow-volume`) and mount path (`/data`).

2. **In Railway Dashboard → Joiner service:**
   - **Volumes:** Add the SAME volume used by EngageFlow.
   - Mount path: `/data` (must match EngageFlow).
   - If Joiner has its own volume for joiner.db, keep it. Ensure:
     - `ENGAGEFLOW_DB_PATH=/data/engageflow.db` (shared file)
     - `JOINER_DB_PATH=/data/joiner.db` (joiner-specific, can stay on same volume)

3. **Joiner service variables:**
   ```
   ENGAGEFLOW_DB_PATH=/data/engageflow.db
   RAILWAY=true
   JOINER_DB_PATH=/data/joiner.db
   ```

4. **Remove Joiner's separate engageflow volume** if it had one. Ensure Joiner only reads from the shared EngageFlow volume for `engageflow.db`.

5. **Redeploy Joiner.**

### If Railway Cannot Mount One Volume to Two Services

**STOP.** Do not use workarounds. Proceed to Option 2 (cookie sync API).

---

## Phase 3 — Concurrency Safety (SQLite)

### EngageFlow Backend

**Already enabled.** `backend/app.py` lines 311–313:

```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout = 30000")
conn.execute("PRAGMA synchronous = NORMAL")
```

### Joiner

**JoinerDb:** Already has WAL (`joiner/backend/db.js` line 57):
```javascript
joinerDb.pragma('journal_mode = WAL');
```

**EngageFlowDb:** Add pragmas for shared access. In `joiner/backend/db.js`, after `engageflowDb = new Database(...)`:

```javascript
engageflowDb.pragma('journal_mode = WAL');
engageflowDb.pragma('busy_timeout = 5000');
```

This prevents "database is locked" when both services access the same file.

---

## Phase 4 — Verify After Change

1. **Joiner /api/profiles** — profiles with cookies in EngageFlow DB should show `auth_status: connected`:

```bash
curl -sS "https://joiner-dev.up.railway.app/api/profiles" | jq '.[] | {email, auth_status, has_cookie_json: (.cookie_json != null)}'
```

2. **DB counts** — both services should report same `profiles_count` and `profiles_with_cookie_json`:

```bash
curl -sS "https://engageflow-dev.up.railway.app/debug/dbinfo" | jq
curl -sS "https://joiner-dev.up.railway.app/debug/dbinfo" | jq
```

3. **Test Auth** — Click "Test Auth" on a connected account. Should succeed.

4. **Logs** — No `SQLITE_BUSY` or `database is locked` errors.

---

## Phase 5 — Rollback Plan

If anything goes wrong:

1. **Detach shared volume from Joiner** — Remove the EngageFlow volume from Joiner service.
2. **Restore Joiner's original volume** — Re-add Joiner's dedicated volume.
3. **Joiner variables:**
   ```
   ENGAGEFLOW_DB_PATH=/data/engageflow.db
   ```
   (Joiner's own `/data` on its dedicated volume)
4. **Redeploy Joiner.**

Joiner will revert to syncing from EngageFlow API (no `cookie_json`). Accounts will show "Missing Cookies" until Connect/Paste is used again.

---

## Summary

| Item | Status |
|------|--------|
| Baseline commit | `d05e138` on dev |
| EngageFlow /debug/dbinfo | Added (gated by ENGAGEFLOW_DEBUG=1) |
| Joiner /debug/dbinfo | Patch provided (apply if joiner in separate repo) |
| WAL/busy_timeout EngageFlow | Already enabled |
| WAL/busy_timeout Joiner engageflowDb | Patch provided |
| Railway config | Manual steps in Phase 2 |

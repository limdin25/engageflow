# EngageFlow Option 1 — Finish Report

**Date:** 2026-03-04  
**Status:** Phase 1–2 complete. **Phase 3 BLOCKED** — Railway does not support shared volumes.

---

## 1) Joiner Source Location (Phase 1 — PROVEN)

| Item | Value |
|------|-------|
| **Repo** | https://github.com/limdin25/engageflow |
| **Path** | `joiner/` (monorepo subdirectory) |
| **Branch** | `main` has Railway integration (config-loader, config.railway.js) |
| **Evidence** | `git ls-tree origin/main` → `joiner` tree; `git ls-tree origin/dev` → `joiner` tree |
| **Railway Joiner** | https://joiner-dev.up.railway.app — responds `{"status":"ok","service":"joiner"}` |

**Conclusion:** Joiner is in the engageflow monorepo. Railway joiner is deployed from this repo (likely `main` branch for Railway-specific config).

---

## 2) Joiner Baseline Commit (Before Patch)

| Item | Value |
|------|-------|
| **Commit** | `1114597` |
| **Message** | `joiner: baseline from main (Railway integration, config-loader)` |

---

## 3) Joiner Patch Commit

| Item | Value |
|------|-------|
| **Commit** | `314cabb` |
| **Message** | `joiner: add dbinfo + sqlite WAL for shared db` |
| **Files** | `joiner/backend/db.js`, `joiner/backend/server.js` |

**Changes:**
- **db.js:** `engageflowDb.pragma('journal_mode = WAL')`, `synchronous = NORMAL`, `busy_timeout = 5000`
- **server.js:** `GET /debug/dbinfo` (gated by `ENGAGEFLOW_DEBUG=1`) — returns `db_path`, `file_size_bytes`, `profiles_count`, `profiles_with_cookie_json`

---

## 4) Railway Volume Change — BLOCKER

**Railway does NOT support shared volumes between 2 services.**

**Evidence:**
- [Railway Help Station](https://station.railway.com/questions/attach-same-volume-to-2-different-servic-0e92fc08): *"unfortunately you can't add two volumes to the same service or have a shared volume between 2 services"*
- Web search: "Railway does not support shared volumes between multiple services"

**Implication:** Option 1 (mount EngageFlow volume into Joiner) **cannot be implemented** on Railway. Proceed to **Option 2** (cookie sync API) or **Option 3** (user manually Connect/Paste per account).

---

## 5) dbinfo Outputs (After Deploy)

**Prerequisites:** Set `ENGAGEFLOW_DEBUG=1` on both EngageFlow and Joiner services, redeploy.

**EngageFlow:**
```bash
curl -sS https://engageflow-dev.up.railway.app/debug/dbinfo | jq
```

**Joiner:**
```bash
curl -sS https://joiner-dev.up.railway.app/debug/dbinfo | jq
```

**Expected (before shared volume — NOT POSSIBLE):**
- EngageFlow: `db_path: /data/engageflow.db`, `profiles_with_cookie_json: N`
- Joiner: `db_path: /data/engageflow.db` (joiner's own volume), `profiles_with_cookie_json: M` (M ≤ N, often 0 due to API sync)

**Success conditions (if shared volume were possible):**
- `db_path` identical on both
- `file_size_bytes` matches (or near-identical)
- `profiles_count` matches
- `profiles_with_cookie_json` matches

---

## 6) Pass/Fail Against Success Conditions

| Condition | Status |
|-----------|--------|
| Joiner source found | **PASS** — engageflow repo, joiner/ |
| Joiner baseline commit | **PASS** |
| Joiner patch commit | **PASS** — 314cabb |
| Shared volume mount | **FAIL** — Railway limitation |
| dbinfo on both services | **PENDING** — deploy + set ENGAGEFLOW_DEBUG=1 |
| Prove same DB file | **N/A** — blocked |

---

## 7) Rollback Instructions

**If Joiner patch causes issues:**

```bash
git revert 314cabb --no-edit
git push origin dev
```

Redeploy Joiner. `/debug/dbinfo` will be removed. WAL pragmas on engageflowDb are low-risk; revert only if needed.

**If EngageFlow dbinfo causes issues:**

```bash
git revert 406f2c0 --no-edit
git push origin dev
```

---

## 8) Next Steps (Option 2)

Since Option 1 is blocked:

1. **Option 2 — Cookie sync API:** EngageFlow backend adds `GET /profiles/:id/cookie-json` (or internal sync). Joiner fetches cookie_json on startup/sync.
2. **Option 3 — User action:** Users Connect or Paste Cookies per account on Railway. No code change.

---

## Commands Reference

```bash
# Phase 1 evidence (after ENGAGEFLOW_DEBUG=1 + redeploy)
curl -sS https://engageflow-dev.up.railway.app/debug/dbinfo | jq
curl -sS https://joiner-dev.up.railway.app/debug/dbinfo | jq

# Profiles with cookie status
curl -sS "https://joiner-dev.up.railway.app/api/profiles" | jq '.[] | {email, auth_status, has_cookie_json: (.cookie_json != null)}'
```

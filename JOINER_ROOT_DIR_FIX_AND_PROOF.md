# Joiner Service — Fix Root Directory, Then Prove

## Current State (before fix)

Joiner service is deploying the **wrong app** (EngageFlow Python image). Proof:

| Check | Current result |
|-------|----------------|
| A) GET / | `{"detail":"Not Found"}` (FastAPI) |
| A) GET /api/profiles | `[]` |
| B) X-Joiner-Git-Sha | (no header) |
| C) /debug/routes | null / wrong app |
| D) POST /internal/joiner/sync-cookies | HTTP 404, `{"detail":"Not Found"}` |

**Cause:** Joiner service Source has no (or wrong) **Root Directory**, so it builds from repo root → EngageFlow Dockerfile.

---

## STEP 1 — Fix Source (Railway UI, Joiner service)

**Joiner** → **Settings** → **Source**

Set exactly:

| Field | Value |
|-------|--------|
| Repo | `limdin25/engageflow` |
| Branch | `dev` |
| **Root Directory** | **`joiner/backend`** |
| Build | Dockerfile |

**Save.**

---

## STEP 2 — Build log proof

**Joiner** → **Deployments** → latest deployment → **Build Logs**

Copy 10–15 lines that show:
- Branch: dev
- Commit SHA (27f95a7 or 0155f64 or newer)
- Build context / root directory = joiner/backend
- Dockerfile path = joiner/backend/Dockerfile

```
[PASTE BUILD LOG EXCERPT HERE]
```

---

## STEP 3 — Redeploy

Redeploy Joiner. If **Disable build cache** is available, use it.

---

## STEP 4 — Live proof (run after deploy)

**A) Health / service identity**
```bash
curl -sS https://joiner-dev.up.railway.app/
curl -sS https://joiner-dev.up.railway.app/api/profiles | head -c 200
```
**Expected:** `{"status":"ok","service":"joiner","api":"/api/profiles"}` and non-empty profiles JSON (not `[]` and not `{"detail":"Not Found"}`).

**B) Version header**
```bash
curl -sS -i https://joiner-dev.up.railway.app/ | grep -i x-joiner-git-sha
```
**Expected:** `x-joiner-git-sha: <sha>` (e.g. 0155f64...).

**C) Routes** (Joiner must have `ENGAGEFLOW_DEBUG=1`)
```bash
curl -sS https://joiner-dev.up.railway.app/debug/routes | jq '.git_sha, (.routes[] | select(.path=="/internal/joiner/sync-cookies"))'
```
**Expected:** git_sha string and `{"method":"POST","path":"/internal/joiner/sync-cookies"}`.

**D) Sync endpoint**
```bash
curl -i -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" https://joiner-dev.up.railway.app/internal/joiner/sync-cookies
```
**Expected:** HTTP 200 and body `{ "success": true, "scanned": 3, "updated": N }`.

---

## STEP 5 — Cleanup

Remove **ENGAGEFLOW_DEBUG=1** from Joiner variables. Redeploy.

---

## Output checklist (fill after UI fix)

| # | Item | Your proof |
|---|------|------------|
| 1 | Joiner Source (repo/branch/root dir/build) | [ ] Screenshot or copied text |
| 2 | Build log (joiner/backend + Dockerfile) | [ ] 10–15 lines pasted |
| 3 | curl A–D | [ ] Paste outputs (or say “run the curls in JOINER_ROOT_DIR_FIX_AND_PROOF” and I’ll run them) |
| 4 | Cleanup | [ ] ENGAGEFLOW_DEBUG=1 removed |

**No further “next steps” without 1–3 and passing curl A–D.**

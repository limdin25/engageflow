# PHASE 2 — STEP 1 VPS SNAPSHOT PROOF (PASSED)

**VPS:** 38.242.229.161 (root)  
**Workspace:** `/root/.openclaw/workspace-margarita/engageflow/`

---

## DB_PATH used

```
/root/.openclaw/workspace-margarita/engageflow/backend/engageflow.db
```

*(No `/root/engageflow-shared/` on this host; live DB is in workspace `backend/`.)*

---

## integrity_check output

```
ok
```

---

## Archive size (DB only, after PRAGMA checkpoint(TRUNCATE))

```
676K	/root/engageflow_db_vps.tar.gz
```

---

## ls -la of archive

```
-rw-r--r-- 1 root root 690757 Mar  5 10:30 /root/engageflow_db_vps.tar.gz
```

---

## Optional full archive (DB + WAL + SHM)

- **Path:** `/root/engageflow_db_vps_full.tar.gz`
- **Size:** 1.9M

For Railway restore, the **DB-only** archive (`engageflow_db_vps.tar.gz`) is sufficient after checkpoint.

---

**Step 1 PASSED.** Proceed with Phase 2 restore into Railway volume `/data` for:

- ENGAGEFLOW_NEW_URL=https://engageflow-dev-ec26.up.railway.app  
- JOINER_NEW_URL=https://joiner-dev.up.railway.app  
- FRONTEND_NEW_URL=https://engageflow-front-dev.up.railway.app  

**Next:** Backup current Railway `/data` (Step 3), then restore this VPS archive into `/data` (Step 4), redeploy, run proof (Steps 5–7).

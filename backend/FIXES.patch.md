# EngageFlow – Audit Fix Implementation Guide

Branch: `fix/profile-rotation-auth-timing-activity-feed`  
Target files: `backend/automation/engine.py`, `backend/app.py`

---

## Fix 1 – Profile rotation (`app.py` → `_sync_skool_chats_into_db`)

**Root cause:** `profile_last_attempt[profile_id]` is written when a profile sync starts but is skipped when the loop exits early (Playwright not available, browser dir missing, sync_error set before the write, etc.). This causes `ordered_profiles[:N]` to always return the same profile.

**Change:** Move (or duplicate) the `profile_last_attempt[profile_id] = now_ts` write to the **top** of the per-profile loop body — before any `continue` or early-return guard.

```python
# BEFORE (typical pattern — write only on happy path):
for profile in selected_profiles:
    profile_id = ...
    if not browser_dir.exists():
        continue          # ← profile_last_attempt NOT updated
    profile_last_attempt[profile_id] = now_ts   # ← buried here
    ...

# AFTER — write unconditionally at loop entry:
for profile in selected_profiles:
    profile_id = ...
    now_ts = time.time()
    profile_last_attempt[profile_id] = now_ts   # ← always runs first
    if not browser_dir.exists():
        continue
    ...
```

**Do NOT change:** `ordered_profiles` sort, `profile_last_attempt`-based ordering, `SKOOL_CHAT_PROFILES_PER_SYNC` slice, or `profile_cursor` (leave dead, no new usage).

---

## Fix 2a – Auth marker timing (`app.py` → `_goto_skool_entry_page`)

**Location:** The `page.wait_for_timeout(1800)` inside the `for url in attempts:` loop, just before `return True, url`.

```python
# BEFORE:
page.wait_for_timeout(1800)
return True, url

# AFTER:
try:
    page.wait_for_selector(
        "div[class*='TopNav'], button[class*='ChatNotificationsIconButton'], a[href^='/@']",
        timeout=1800,
        state="visible",
    )
except Exception:
    pass
return True, url
```

---

## Fix 2b – Auth marker timing (`engine.py` → `SkoolSessionManager.validate_session`)

**Location:** Inside `validate_session`, the `self.page.wait_for_timeout(LOGIN_CHECK_POST_LOAD_WAIT_MS)` call after the `networkidle` wait.

```python
# BEFORE:
self.page.wait_for_timeout(LOGIN_CHECK_POST_LOAD_WAIT_MS)

# AFTER:
try:
    self.page.wait_for_selector(
        "div[class*='TopNav'], button[class*='ChatNotificationsIconButton'], a[href^='/@']",
        timeout=LOGIN_CHECK_POST_LOAD_WAIT_MS,
        state="visible",
    )
except Exception:
    pass
```

All other logic in `validate_session` remains unchanged.

---

## Fix 3a – Activity feed profile name (`engine.py` → `_persist_activity_rows` + all `activity_feed` writes)

**Root cause:** `activity_feed.profile` is written with a runtime display name (e.g. `"marknoah2024"`) while `profiles.name` in the DB stores the full email (`"marknoah2024@gmail.com"`). The frontend JOIN on `activity_feed.profile = profiles.name` returns no rows.

**Change:** In `_persist_activity_rows`, ensure the resolved `profiles.name` from the DB is used, not `profile.get("label")` or any other derived key.

```python
# Pattern to verify / enforce:
# When inserting into activity_feed, the 'profile' column must come from:
db_profile_name = db.execute(
    "SELECT name FROM profiles WHERE id = ?", (profile_id,)
).fetchone()["name"]  # e.g. "marknoah2024@gmail.com"

# NOT from:
# profile.get("label")      ← display label, may be short form
# profile.get("name")       ← raw dict field, may differ from DB canonical
# profile_name variable     ← verify this was resolved from DB, not passed in
```

Add inline comment where the name is resolved:
```python
# Use canonical profiles.name from DB to match frontend JOIN on activity_feed.profile
```

Trace ALL other INSERT/UPDATE paths into `activity_feed` in both `engine.py` and `app.py` and apply the same guard.

---

## Fix 3b – Log buffering (`app.py` → `_insert_backend_log` + new flush infrastructure)

### Step 1 – Add module-level buffer (place near other module-level state, e.g. near `_SKOOL_CHAT_IMPORT_CACHE`)

```python
_LOG_BUFFER: List[Dict[str, Any]] = []
_LOG_BUFFER_LOCK = threading.Lock()
```

### Step 2 – Modify the lock-error handler in `_insert_backend_log`

```python
# BEFORE (in the outer except sqlite3.OperationalError):
except sqlite3.OperationalError as exc:
    if "locked" in str(exc).lower():
        LOGGER.warning("Skipped log write due to sqlite lock: profile=%s status=%s", profile, status)
        return
    raise

# AFTER:
except sqlite3.OperationalError as exc:
    if "locked" in str(exc).lower():
        with _LOG_BUFFER_LOCK:
            _LOG_BUFFER.append({
                "profile": profile,
                "status": status,
                "module": module_value,
                "action": action_value,
                "message": normalized_message,
                "ts": now_display_time(),
            })
        LOGGER.warning(
            "Buffered log write due to sqlite lock: profile=%s status=%s (buffer_size=%d)",
            profile, status, len(_LOG_BUFFER),
        )
        return
    raise
```

### Step 3 – Add flush function

```python
def _flush_log_buffer(db: sqlite3.Connection) -> int:
    """Retry buffered log entries that failed due to SQLite lock contention."""
    with _LOG_BUFFER_LOCK:
        if not _LOG_BUFFER:
            return 0
        pending = list(_LOG_BUFFER)
        _LOG_BUFFER.clear()

    flushed = 0
    requeue: List[Dict[str, Any]] = []
    for entry in pending:
        try:
            try:
                _db_execute_with_retry(
                    db,
                    "INSERT INTO logs (id, timestamp, profile, status, module, action, message, fallbackLevelUsed) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        entry["ts"],
                        entry["profile"],
                        entry["status"],
                        entry["module"],
                        entry["action"],
                        entry["message"],
                        None,
                    ),
                )
            except sqlite3.OperationalError as exc:
                if "no column named module" not in str(exc).lower() and "no column named action" not in str(exc).lower():
                    raise
                _db_execute_with_retry(
                    db,
                    "INSERT INTO logs (id, timestamp, profile, status, message, fallbackLevelUsed) VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), entry["ts"], entry["profile"], entry["status"], entry["message"], None),
                )
            _db_commit_with_retry(db)
            flushed += 1
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower():
                requeue.append(entry)
            # non-lock errors are dropped (stale entries, schema mismatch)

    if requeue:
        with _LOG_BUFFER_LOCK:
            _LOG_BUFFER[:0] = requeue  # prepend so ordering is preserved

    if flushed > 0:
        LOGGER.debug("Flushed %d buffered log entries", flushed)
    return flushed
```

### Step 4 – Call flush at end of sync

In `_sync_skool_chats_to_inbox` (or `_sync_skool_chats_into_db`), add at the end, after the main sync work completes:

```python
# Flush any log entries buffered during lock-contention windows.
try:
    with get_db() as db:
        _flush_log_buffer(db)
except Exception:
    pass  # non-critical, next sync will retry
```

---

## Verification Checklist

- [ ] Run with 2+ profiles; confirm each profile gets synced in rotation (not always the first one)
- [ ] Confirm no `wait_for_timeout` calls remain in `_goto_skool_entry_page` or `validate_session`
- [ ] Trigger a lock-contention scenario (heavy write load); confirm logs appear in the Logs page after the buffer flushes
- [ ] After a full automation run, confirm Activity Timeline shows activity rows for all active profiles (not just one)
- [ ] Search `activity_feed` in DB: confirm `profile` column values match `profiles.name` exactly (full email)

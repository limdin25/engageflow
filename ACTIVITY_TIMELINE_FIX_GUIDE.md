# Activity Timeline Complete Fix Guide

## Problem 1: Activities Not Showing in Timeline
**Status**: ✅ FIXED by ORDER BY timestamp DESC

## Problem 2: Scheduled Actions Not Executing
**Status**: 🔴 NEEDS FIX

### Root Cause
The "Next action in 4m 58s" countdown is **display-only**. The scheduler daemon needs to:
1. Actually execute the action when time arrives
2. Log the execution to Activity Timeline
3. Update the queue item status

---

## Backend Fix Required

### Location: `backend/automation/engine.py` or `backend/app.py`

Find the scheduler loop and ensure it:

```python
# REQUIRED: Scheduler must log to Activity Timeline when executing actions

def execute_scheduled_action(queue_item):
    """Execute a queued action and log to Activity Timeline"""
    try:
        # Execute the action (comment, like, etc.)
        result = perform_action(queue_item)
        
        # CRITICAL: Log to Activity Timeline
        with get_db() as db:
            db.execute(
                """
                INSERT INTO logs (id, timestamp, profile, status, module, action, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    now_display_time(),  # This creates the timestamp
                    queue_item['profileName'],
                    'success',
                    'queue',
                    'execute',
                    f"Executed action: {queue_item['action']} on {queue_item['postUrl']}"
                )
            )
            db.commit()
            
        return result
    except Exception as e:
        # Log failure to Activity Timeline
        with get_db() as db:
            db.execute(
                """
                INSERT INTO logs (id, timestamp, profile, status, module, action, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    now_display_time(),
                    queue_item['profileName'],
                    'error',
                    'queue',
                    'execute',
                    f"Failed to execute action: {str(e)}"
                )
            )
            db.commit()
```

### Scheduler Loop Enhancement

```python
# In the main scheduler loop
while scheduler_running:
    with get_db() as db:
        # Get actions that are due NOW
        now = datetime.now()
        due_items = db.execute(
            """
            SELECT * FROM queue_items 
            WHERE scheduledFor <= ? 
            AND status = 'pending'
            ORDER BY scheduledFor ASC
            LIMIT 10
            """,
            (now.isoformat(),)
        ).fetchall()
        
        for item in due_items:
            # Mark as running
            db.execute(
                "UPDATE queue_items SET status = 'running' WHERE id = ?",
                (item['id'],)
            )
            db.commit()
            
            # Execute and log
            execute_scheduled_action(item)
            
            # Mark as completed
            db.execute(
                "UPDATE queue_items SET status = 'completed' WHERE id = ?",
                (item['id'],)
            )
            db.commit()
    
    # Sleep for 1 second before checking again
    time.sleep(1)
```

---

## Quick Diagnostic

### Check if Scheduler is Running
```bash
cd ~/engageflow/backend
grep -n "scheduler\|queue_items" app.py | head -20
```

### Check Queue Items Database
```bash
cd ~/engageflow/backend
sqlite3 engageflow.db "SELECT id, action, scheduledFor, status FROM queue_items WHERE status = 'pending' LIMIT 5;"
```

### Check if Actions are Being Executed
```bash
# Watch backend logs in real-time
cd ~/engageflow/backend
tail -f logs/engageflow.log | grep -i "queue\|execute\|scheduled"
```

---

## Testing After Fix

1. **Create a test action:**
   - Go to Queue tab
   - Schedule a comment for 1 minute from now
   - Note the exact scheduled time

2. **Monitor execution:**
   - Watch Activity Timeline
   - When countdown reaches 0, activity should appear
   - Refresh page - activity should still be visible at TOP

3. **Verify logs:**
   ```bash
   cd ~/engageflow/backend
   sqlite3 engageflow.db "SELECT * FROM logs ORDER BY timestamp DESC LIMIT 5;"
   ```

---

## Files to Check/Modify

1. **`backend/automation/engine.py`** - Main scheduler logic
2. **`backend/app.py`** - Queue execution endpoints
3. **`backend/engageflow.db`** - logs table (should auto-populate)

---

## Expected Behavior After Fix

✅ Countdown timer shows "Next action in 4m 58s"
✅ Timer counts down to 0
✅ Action executes automatically
✅ Activity appears in Activity Timeline immediately
✅ Activity stays at TOP after page refresh
✅ Queue item marked as 'completed'

---

## Current Status

- [x] Frontend limit increased to 500
- [x] Backend ORDER BY fixed (timestamp DESC)
- [x] Database index added
- [ ] **Scheduler actually executing actions** ← NEEDS THIS
- [ ] **Logging executions to Activity Timeline** ← NEEDS THIS

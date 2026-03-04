"""
Diagnostic tests for automation lifecycle: task execution, queue state, activity persistence.
"""
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables
from automation.engine import AutomationEngine
from tests.helpers import seed_profile, seed_queue_items, seed_activity_feed


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def engine(tmp_path):
    db_path = tmp_path / "test_engageflow.db"
    ensure_tables()
    eng = AutomationEngine(db_path, Path(__file__).parent.parent)
    eng._hydrate_state_from_disk()
    return eng


def test_task_lifecycle_emit_trace(engine):
    """TASK_PICKED, TASK_STARTED, TASK_COMPLETED, TASK_FAILED, ACTIVITY_LOGGED appear in trace."""
    engine._emit_lifecycle("TASK_PICKED", task_id="t1", profile_id="p1", action_type="comment", state="picked")
    engine._emit_lifecycle("TASK_STARTED", task_id="t1", profile_id="p1", action_type="comment", state="running")
    engine._emit_lifecycle("TASK_COMPLETED", task_id="t1", profile_id="p1", action_type="comment", state="completed")
    engine._emit_lifecycle("TASK_FAILED", task_id="t2", profile_id="p2", action_type="comment", state="failed", error="timeout")
    engine._emit_lifecycle("ACTIVITY_LOGGED", task_id="post-url", profile_id="p1", action_type="Commented", state="persisted")

    trace = list(engine._lifecycle_trace)
    events = [e["event"] for e in trace]
    assert "TASK_PICKED" in events
    assert "TASK_STARTED" in events
    assert "TASK_COMPLETED" in events
    assert "TASK_FAILED" in events
    assert "ACTIVITY_LOGGED" in events
    failed = next(e for e in trace if e["event"] == "TASK_FAILED")
    assert failed.get("state") == "failed"
    assert "timeout" in str(failed.get("error", ""))


def test_activity_logged_after_action(client):
    """When activity_feed gets a new row, GET /activity returns it and sorts newest first."""
    with get_db() as db:
        name = seed_profile(db, "testprofile")
        seed_activity_feed(db, name, 2, utc=True)
    r = client.get("/activity?limit=10")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    assert data[0].get("profile") == name
    assert "timestamp" in data[0]
    # Newest first
    if len(data) >= 2:
        ts0 = data[0].get("timestamp", "")
        ts1 = data[1].get("timestamp", "")
        assert ts0 >= ts1 or ts0 == ts1


def test_queue_state_updates(client):
    """_remove_queue_item removes item from queue_items table."""
    ensure_tables()
    with get_db() as db:
        pid = "test-profile-id"
        post_url = "https://skool.com/group/post-123"
        t = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        db.execute(
            """INSERT INTO queue_items (id, profile, profileId, community, communityId, postId, keyword, keywordId, scheduledTime, scheduledFor, priorityScore, countdown)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), "Profile", pid, "comm", "cid", post_url, "kw", "kid", t, t, 50, 60),
        )
        db.commit()
        before = db.execute("SELECT COUNT(*) AS cnt FROM queue_items WHERE profileId = ?", (pid,)).fetchone()["cnt"]
        assert before == 1

    engine = client.app.state.automation_engine
    engine._remove_queue_item(pid, post_url)

    with get_db() as db:
        after = db.execute("SELECT COUNT(*) AS cnt FROM queue_items WHERE profileId = ?", (pid,)).fetchone()["cnt"]
        assert after == 0


def test_api_logs_returns_lifecycle_entries(client):
    """GET /api/logs returns last N automation lifecycle trace entries."""
    r = client.get("/api/logs?limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data.get("success") is True
    assert "entries" in data
    assert "count" in data
    assert isinstance(data["entries"], list)


def test_activity_query_orders_desc(client):
    """GET /activity reads activity_feed and sorts ORDER BY timestamp DESC."""
    with get_db() as db:
        name = seed_profile(db, "activity_order_test")
        base = datetime.now(timezone.utc)
        for i in range(5):
            ts = (base - timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            db.execute(
                """INSERT INTO activity_feed (id, profile, groupName, action, timestamp, postUrl)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), name, "group", "Commented", ts, f"https://x.com/p{i}"),
            )
        db.commit()

    r = client.get("/activity?limit=10&profile=activity_order_test")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 5
    timestamps = [d.get("timestamp", "") for d in data[:5]]
    assert timestamps == sorted(timestamps, reverse=True)

    with get_db() as db:
        db.execute("DELETE FROM activity_feed WHERE profile = ?", (name,))
        db.execute("DELETE FROM profiles WHERE name = ?", (name,))
        db.commit()

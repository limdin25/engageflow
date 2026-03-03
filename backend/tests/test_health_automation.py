"""
TDD: /health endpoint and ENGAGEFLOW_AUTOMATION_ENABLED behavior.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables
from automation.engine import AutomationEngine
from tests.helpers import seed_profile, seed_queue_items


@pytest.fixture
def client():
    """TestClient as context manager so lifespan runs and app.state.automation_engine exists."""
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_health_running_false_when_disabled(client):
    """GET /health returns running=false when scheduler not started."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("running") is False


def test_health_running_true_when_scheduler_started(client):
    """GET /health returns running=true after POST /automation/start."""
    async def _mock_start(self, profiles=None, global_settings=None):
        self._state.is_running = True
        return {"success": True, "isRunning": True}

    with get_db() as db:
        seed_profile(db, "testprofile")
        seed_queue_items(db, 3)
    with patch.object(AutomationEngine, "start", _mock_start):
        r_start = client.post("/automation/start", json={})
        assert r_start.status_code == 200
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert data.get("running") is True
        client.post("/automation/stop")


def test_activity_updates_when_action_executes(client):
    """When activity_feed gets a new row, GET /activity returns it newest-first."""
    from tests.helpers import seed_activity_feed

    with get_db() as db:
        name = seed_profile(db, "testprofile")
        seed_activity_feed(db, name, 2, utc=True)
    r1 = client.get("/activity?limit=5")
    assert r1.status_code == 200
    initial = r1.json()
    assert len(initial) >= 2
    newest_ts = initial[0].get("timestamp", "")

    with get_db() as db:
        import uuid
        from datetime import datetime, timezone, timedelta
        # Use future timestamp so new row is newest (seed uses base, base+1min)
        ts_new = (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        db.execute(
            """INSERT INTO activity_feed (id, profile, groupName, action, timestamp, postUrl)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), name, "group", "Commented", ts_new, "https://x.com/p-new"),
        )
        db.commit()

    r2 = client.get("/activity?limit=5")
    assert r2.status_code == 200
    updated = r2.json()
    assert len(updated) >= 3
    assert updated[0].get("postUrl") == "https://x.com/p-new"
    assert updated[0].get("timestamp") >= newest_ts or ts_new in str(updated[0].get("timestamp", ""))

    with get_db() as db:
        db.execute("DELETE FROM activity_feed")
        db.execute("DELETE FROM profiles")
        db.commit()

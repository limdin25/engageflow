"""
TDD: Countdown must persist across refresh (Entry #37).
Bug: UI shows "Next action in 4m 58s", on refresh resets to 5 minutes.
Root cause: Frontend falls back to engineStatus.countdownSeconds when queue parse fails;
backend countdown reflects scheduler loop wait, not queue item schedule.
Fix: Backend returns nextScheduledFor + countdown from queue when running.
"""
import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables
from tests.helpers import seed_profile, seed_queue_items


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_automation_status_contract_includes_next_scheduled_for(client):
    """GET /automation/status response includes nextScheduledFor key (nullable when no queue)."""
    r = client.get("/automation/status")
    assert r.status_code == 200
    data = r.json()
    assert "countdownSeconds" in data
    assert "nextScheduledFor" in data


def test_activity_returns_newest_first(client):
    """GET /activity returns newest first (ORDER BY timestamp DESC)."""
    with get_db() as db:
        name = seed_profile(db, "activity_order")
        db.execute(
            "INSERT INTO activity_feed (id, profile, groupName, action, timestamp, postUrl) VALUES (?, ?, ?, ?, ?, ?)",
            ("a1", name, "g", "Commented", "2026-03-04T10:00:00Z", "https://x.com/1"),
        )
        db.execute(
            "INSERT INTO activity_feed (id, profile, groupName, action, timestamp, postUrl) VALUES (?, ?, ?, ?, ?, ?)",
            ("a2", name, "g", "Commented", "2026-03-04T11:00:00Z", "https://x.com/2"),
        )
        db.commit()
    r = client.get("/activity?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    first_ts = data[0].get("timestamp", "")
    second_ts = data[1].get("timestamp", "")
    assert first_ts >= second_ts or "2026-03-04T11" in first_ts
    with get_db() as db:
        db.execute("DELETE FROM activity_feed")
        db.execute("DELETE FROM profiles")
        db.commit()

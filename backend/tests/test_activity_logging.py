"""
TDD: Activity logging when comments are posted.
Entry #34: Activity persisted immediately after comment post, before verify.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app import app, get_db, ensure_tables, AUTOMATION_SETTINGS_DEFAULT
from tests.helpers import seed_profile


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_activity_timestamp_is_utc(client):
    """Activity timestamps must be UTC and parseable by frontend."""
    with get_db() as db:
        name = seed_profile(db, "activity_log_test")
        db.execute(
            """INSERT INTO activity_feed (id, profile, groupName, action, timestamp, postUrl)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), name, "group", "Commented", "2026-03-04T14:30:00.000000Z", "https://skool.com/p1"),
        )
        db.commit()

    r = client.get("/activity?limit=1")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        ts = data[0].get("timestamp", "")
        assert "Z" in ts or "+" in ts, f"Timestamp should be UTC: {ts!r}"

    with get_db() as db:
        db.execute("DELETE FROM activity_feed")
        db.execute("DELETE FROM profiles")
        db.commit()


def test_settings_update_returns_200_on_db_error(client):
    """PUT /automation/settings must return 200 with success:false on DB error, not 500."""
    from contextlib import contextmanager

    @contextmanager
    def failing_db():
        raise Exception("DB unavailable")

    def failing_get_db():
        return failing_db()

    payload = AUTOMATION_SETTINGS_DEFAULT.model_dump()
    with patch("app.get_db", failing_get_db):
        r = client.put("/automation/settings", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body.get("success") is False
    assert body.get("error") == "settings_update_failed"
    assert "DB unavailable" in body.get("message", "")

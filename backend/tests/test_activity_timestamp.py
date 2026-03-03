"""
TDD: Activity timestamp normalization for frontend parseISO.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables
from tests.helpers import seed_profile


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_activity_timestamp_normalized_with_z_suffix(client):
    """GET /activity returns timestamps with Z suffix for unambiguous UTC parsing."""
    with get_db() as db:
        name = seed_profile(db, "testprofile")
        # Insert row with ISO timestamp WITHOUT timezone (legacy format)
        db.execute(
            """INSERT INTO activity_feed (id, profile, groupName, action, timestamp, postUrl)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), name, "group", "Commented", "2025-03-03T04:50:53.850948", "https://x.com/p1"),
        )
        db.commit()

    r = client.get("/activity?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    ts = data[0].get("timestamp", "")
    assert ts.endswith("Z"), f"Timestamp must end with Z for UTC: got {ts!r}"

    with get_db() as db:
        db.execute("DELETE FROM activity_feed")
        db.execute("DELETE FROM profiles")
        db.commit()

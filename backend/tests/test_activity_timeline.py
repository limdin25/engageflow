"""
TDD: Activity limit 100 + UTC timestamps.
- read_activity returns at most 100 items by default.
- Activity timestamps from engine use UTC (Z or +00:00).
"""
import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables, read_activity
from tests.helpers import seed_activity_feed, seed_profile


@pytest.fixture
def client():
    ensure_tables()
    return TestClient(app)


@pytest.fixture
def seed_150_activity_items(client):
    """Seed 1 profile + 150 activity items so unfixed read_activity would return >100."""
    with get_db() as db:
        name = seed_profile(db, "testprofile")
        seed_activity_feed(db, name, 150, utc=True)
    yield
    with get_db() as db:
        db.execute("DELETE FROM activity_feed")
        db.execute("DELETE FROM profiles")
        db.commit()


def test_read_activity_returns_at_most_100_by_default(client, seed_150_activity_items):
    """Without limit, activity could return 150. With limit=100, must return <=100."""
    result = read_activity()
    assert len(result) <= 100, f"read_activity() returned {len(result)} items, expected <=100"


def test_activity_api_returns_at_most_100(client, seed_150_activity_items):
    """GET /activity returns at most 100 items."""
    r = client.get("/activity")
    assert r.status_code == 200
    data = r.json()
    assert len(data) <= 100, f"GET /activity returned {len(data)} items, expected <=100"


def test_activity_timestamps_use_utc(client, seed_150_activity_items):
    """Activity timestamps must be UTC (end with Z or +00:00)."""
    result = read_activity()
    for item in result:
        ts = getattr(item, "timestamp", "") or ""
        assert "Z" in ts or "+00:00" in ts, f"timestamp {ts!r} is not UTC"

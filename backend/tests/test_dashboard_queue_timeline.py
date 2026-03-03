"""
TDD: Dashboard queue/timeline — queue limit 30, profile interleaving, activity newest-first.
"""
import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables, read_queue, read_activity
from tests.helpers import seed_profile, seed_queue_items, seed_activity_feed


@pytest.fixture
def client():
    ensure_tables()
    return TestClient(app)


def _seed_queue_consecutive_profiles(db, profile_a_count: int, profile_b_count: int):
    """Seed queue so profile A has consecutive items first, then profile B.
    Without interleaving: A,A,...,A,B,B,...,B.
    With interleaving: A,B,A,B,... (no adjacent same profile when both have items).
    """
    from datetime import datetime, timedelta
    import uuid

    base = datetime.now()
    idx = 0
    for _ in range(profile_a_count):
        t = (base + timedelta(minutes=idx)).strftime("%Y-%m-%dT%H:%M:%S")
        db.execute(
            """INSERT INTO queue_items (id, profile, profileId, community, communityId, postId, keyword, keywordId, scheduledTime, scheduledFor, priorityScore, countdown)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), "ProfileA", "pid-A", "comm", "cid", f"postA{idx}", "kw", "kid", t, t, 50, 60),
        )
        idx += 1
    for _ in range(profile_b_count):
        t = (base + timedelta(minutes=idx)).strftime("%Y-%m-%dT%H:%M:%S")
        db.execute(
            """INSERT INTO queue_items (id, profile, profileId, community, communityId, postId, keyword, keywordId, scheduledTime, scheduledFor, priorityScore, countdown)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), "ProfileB", "pid-B", "comm", "cid", f"postB{idx}", "kw", "kid", t, t, 50, 60),
        )
        idx += 1
    db.commit()


@pytest.fixture
def seed_multi_profile_queue(client):
    """Seed 5 from A, 5 from B — consecutive without interleaving would be A,A,A,A,A,B,B,B,B,B."""
    with get_db() as db:
        _seed_queue_consecutive_profiles(db, 5, 5)
    yield
    with get_db() as db:
        db.execute("DELETE FROM queue_items")
        db.commit()


def test_queue_returns_at_most_30(client):
    """GET /queue returns up to 30 items by default."""
    with get_db() as db:
        seed_queue_items(db, 35)
    r = client.get("/queue")
    assert r.status_code == 200
    data = r.json()
    assert len(data) <= 30, f"GET /queue returned {len(data)} items, expected <=30"
    with get_db() as db:
        db.execute("DELETE FROM queue_items")
        db.commit()


def test_queue_interleaves_profiles(client, seed_multi_profile_queue):
    """When queue has items from multiple profiles, no adjacent identical profile when alternatives exist."""
    result = read_queue()
    assert len(result) >= 4, "Need at least 4 items to test interleaving"
    profile_ids = [
        str(getattr(r, "profileId", "") or getattr(r, "profile", ""))
        for r in result
    ]

    # Check: no adjacent same profile when we have at least 2 profiles
    seen = set(profile_ids)
    if len(seen) >= 2:
        for i in range(len(profile_ids) - 1):
            assert profile_ids[i] != profile_ids[i + 1], (
                f"Adjacent same profile at index {i},{i+1}: {profile_ids[i]}"
            )


def test_queue_api_interleaves(client, seed_multi_profile_queue):
    """GET /queue returns interleaved profiles (no adjacent same profile when alternatives exist)."""
    r = client.get("/queue")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 4
    profile_ids = [str(item.get("profileId") or item.get("profile", "")) for item in data]
    seen = set(profile_ids)
    if len(seen) >= 2:
        for i in range(len(profile_ids) - 1):
            assert profile_ids[i] != profile_ids[i + 1], (
                f"Adjacent same profile at index {i},{i+1}: {profile_ids[i]}"
            )


def test_activity_newest_first(client):
    """Activity timeline returns newest-first (descending by timestamp)."""
    with get_db() as db:
        name = seed_profile(db, "testprofile")
        seed_activity_feed(db, name, 20, utc=True)
    result = read_activity()
    assert len(result) >= 2
    # Parse timestamps
    timestamps = []
    for item in result:
        ts = getattr(item, "timestamp", None) or (item.get("timestamp") if isinstance(item, dict) else None)
        timestamps.append(ts)
    # First must be >= second (newest first)
    for i in range(len(timestamps) - 1):
        t0, t1 = timestamps[i], timestamps[i + 1]
        if t0 and t1:
            # Both should be comparable; newest first means t0 >= t1
            from datetime import datetime
            d0 = datetime.fromisoformat(t0.replace("Z", "+00:00"))
            d1 = datetime.fromisoformat(t1.replace("Z", "+00:00"))
            assert d0 >= d1, f"Activity not newest-first: index {i}={t0} should be >= index {i+1}={t1}"
    with get_db() as db:
        db.execute("DELETE FROM activity_feed")
        db.execute("DELETE FROM profiles")
        db.commit()


def test_activity_api_newest_first(client):
    """GET /activity returns newest-first."""
    with get_db() as db:
        name = seed_profile(db, "testprofile")
        seed_activity_feed(db, name, 20, utc=True)
    r = client.get("/activity")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    # Parse timestamps
    for i in range(len(data) - 1):
        t0 = data[i].get("timestamp") or ""
        t1 = data[i + 1].get("timestamp") or ""
        if t0 and t1:
            from datetime import datetime
            d0 = datetime.fromisoformat(t0.replace("Z", "+00:00"))
            d1 = datetime.fromisoformat(t1.replace("Z", "+00:00"))
            assert d0 >= d1, f"Activity not newest-first: index {i}={t0} should be >= index {i+1}={t1}"
    with get_db() as db:
        db.execute("DELETE FROM activity_feed")
        db.execute("DELETE FROM profiles")
        db.commit()

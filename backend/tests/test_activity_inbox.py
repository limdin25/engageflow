"""
TDD: Activity timeline and inbox sync behavior.
"""
import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables
from tests.helpers import seed_profile, seed_activity_feed


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_activity_endpoint_returns_recent(client):
    """GET /activity returns rows ordered by timestamp DESC."""
    with get_db() as db:
        name = seed_profile(db, "acttest")
        seed_activity_feed(db, name, 3, utc=True)
    r = client.get("/activity?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 3
    timestamps = [d["timestamp"] for d in data]
    assert timestamps == sorted(timestamps, reverse=True)


def test_conversations_endpoint_returns_list(client):
    """GET /conversations returns 200 and a list."""
    r = client.get("/conversations")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_conversations_sync_param_no_500(client):
    """GET /conversations?sync=true does not 500."""
    r = client.get("/conversations?sync=true")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

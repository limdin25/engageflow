"""
TDD: /api/db-status endpoint (always available, never 500).
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


def test_db_status_keys_present(client):
    """GET /api/db-status returns expected keys."""
    r = client.get("/api/db-status")
    assert r.status_code == 200
    data = r.json()
    assert "db_path" in data
    assert "db_file_exists" in data
    assert "db_size_bytes" in data
    assert "writable" in data
    assert "last_activity_timestamp" in data
    assert "now_utc" in data


def test_db_status_when_empty_db(client):
    """GET /api/db-status returns 200 when DB is empty."""
    r = client.get("/api/db-status")
    assert r.status_code == 200
    data = r.json()
    assert data["last_activity_timestamp"] is None
    assert data["db_file_exists"] is True
    assert isinstance(data["db_size_bytes"], int)


def test_db_status_when_activity_exists(client):
    """GET /api/db-status returns last_activity_timestamp when activity exists."""
    with get_db() as db:
        name = seed_profile(db, "dbstat")
        seed_activity_feed(db, name, 1, utc=True)
    r = client.get("/api/db-status")
    assert r.status_code == 200
    data = r.json()
    assert data["last_activity_timestamp"] is not None
    assert data["writable"] is True

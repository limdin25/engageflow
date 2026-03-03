"""
TDD: Queue limit 30. GET /queue must return at most 30 items by default.
"""
import pytest
from fastapi.testclient import TestClient

# App import uses ENGAGEFLOW_DB_PATH from conftest
from app import app, get_db, ensure_tables, read_queue
from tests.helpers import seed_queue_items


@pytest.fixture
def client():
    ensure_tables()
    return TestClient(app)


@pytest.fixture
def seed_35_queue_items(client):
    """Seed 35 items so unfixed read_queue would return >30."""
    with get_db() as db:
        seed_queue_items(db, 35)
    yield
    with get_db() as db:
        db.execute("DELETE FROM queue_items")
        db.commit()


def test_read_queue_returns_at_most_30_by_default(client, seed_35_queue_items):
    """Without limit, queue could return 35. With limit=30, must return <=30."""
    result = read_queue()
    assert len(result) <= 30, f"read_queue() returned {len(result)} items, expected <=30"


def test_queue_api_returns_at_most_30(client, seed_35_queue_items):
    """GET /queue returns at most 30 items."""
    r = client.get("/queue")
    assert r.status_code == 200
    data = r.json()
    assert len(data) <= 30, f"GET /queue returned {len(data)} items, expected <=30"

"""
TDD: /debug/scheduler never returns 500.
"""
import pytest
from fastapi.testclient import TestClient

from app import app, ensure_tables


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_scheduler_endpoint_no_500_when_engine_disabled(client):
    """GET /debug/scheduler returns 200 with stable JSON even when engine not running."""
    r = client.get("/debug/scheduler")
    assert r.status_code == 200
    data = r.json()
    assert "success" in data
    assert "running" in data
    assert "paused" in data
    assert data["success"] is True

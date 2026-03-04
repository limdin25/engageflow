"""
TDD: UI contract — /automation/* and /api/automation/* must both work (prefixed and unprefixed).
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables
from automation.engine import AutomationEngine
from tests.helpers import seed_profile, seed_queue_items


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_stop_prefixed_route_ok(client):
    """POST /api/automation/stop returns 200 and isRunning=false."""
    r = client.post("/api/automation/stop")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data.get("success") is True
    assert data.get("isRunning") is False


def test_stop_unprefixed_route_ok(client):
    """POST /automation/stop returns 200 and isRunning=false."""
    r = client.post("/automation/stop")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data.get("success") is True
    assert data.get("isRunning") is False


def test_status_prefixed_route_ok(client):
    """GET /api/automation/status returns 200 with expected keys."""
    r = client.get("/api/automation/status")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert "success" in data
    assert "isRunning" in data


def test_status_unprefixed_route_ok(client):
    """GET /automation/status returns 200 with expected keys."""
    r = client.get("/automation/status")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert "success" in data
    assert "isRunning" in data


def test_stop_idempotent_on_prefixed_route(client):
    """POST /api/automation/stop twice returns 200 both times."""
    r1 = client.post("/api/automation/stop")
    assert r1.status_code == 200
    r2 = client.post("/api/automation/stop")
    assert r2.status_code == 200
    assert r2.json().get("isRunning") is False

"""
TDD: POST /automation/stop contract — 200, running=false, idempotent when already stopped.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables
from automation.engine import AutomationEngine
from tests.helpers import seed_profile, seed_queue_items


@pytest.fixture
def client():
    """TestClient as context manager so lifespan runs and app.state.automation_engine exists."""
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_stop_returns_200_and_sets_running_false(client):
    """POST /automation/stop returns 200 and isRunning=false."""
    async def _mock_start(self, profiles=None, global_settings=None):
        self._state.is_running = True
        return {"success": True, "isRunning": True}

    with get_db() as db:
        seed_profile(db, "testprofile")
        seed_queue_items(db, 3)
    with patch.object(AutomationEngine, "start", _mock_start):
        client.post("/automation/start", json={})
    r_stop = client.post("/automation/stop")
    assert r_stop.status_code == 200, f"Expected 200, got {r_stop.status_code}: {r_stop.text}"
    data = r_stop.json()
    assert data.get("success") is True
    assert data.get("isRunning") is False
    assert data.get("runState") == "idle"
    r_health = client.get("/health")
    assert r_health.json().get("running") is False


def test_stop_idempotent_when_already_stopped(client):
    """POST /automation/stop returns 200 when engine already stopped (idempotent)."""
    r = client.post("/automation/stop")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data.get("success") is True
    assert data.get("isRunning") is False
    r2 = client.post("/automation/stop")
    assert r2.status_code == 200
    assert r2.json().get("isRunning") is False


def test_stop_no_500_when_engine_missing(client):
    """POST /automation/stop must not return 500 when engine not ready (app.state.automation_engine missing)."""
    app = client.app
    engine = getattr(app.state, "automation_engine", None)
    if engine is not None:
        del app.state.automation_engine
    try:
        r = client.post("/automation/stop")
        assert r.status_code != 500, f"Stop must not return 500: {r.text}"
        assert r.status_code == 200
        assert r.json().get("isRunning") is False
    finally:
        if engine is not None:
            app.state.automation_engine = engine


def test_api_diagnostics_returns_required_keys(client):
    """GET /api/diagnostics returns required keys: system_health, database_status, automation_engine_state, last_activity_timestamp, recent_errors, environment_flags."""
    r = client.get("/api/diagnostics")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert "system_health" in data
    assert "database_status" in data
    assert "automation_engine_state" in data
    assert "last_activity_timestamp" in data
    assert "recent_errors" in data
    assert "environment_flags" in data
    assert "status" in data["system_health"]
    assert "running" in data["system_health"]
    assert "db_path" in data["environment_flags"]

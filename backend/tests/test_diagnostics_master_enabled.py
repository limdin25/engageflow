"""Test diagnostics includes db_master_enabled flag."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import app, ensure_tables, get_db
from tests.helpers import seed_profile, seed_queue_items


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as c:
        yield c


def test_diagnostics_db_master_enabled_is_bool_even_when_settings_missing(client: TestClient):
    """GET /api/diagnostics db_master_enabled is always bool, never null."""
    with patch("app._load_or_create_automation_settings", side_effect=Exception("DB unavailable")):
        response = client.get("/api/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "db_master_enabled" in data
    assert isinstance(data["db_master_enabled"], bool)


def test_diagnostics_includes_db_master_enabled(client: TestClient):
    """GET /api/diagnostics must include db_master_enabled from automation_settings."""
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "db_master_enabled" in data
    assert isinstance(data["db_master_enabled"], bool)


def test_stop_sets_db_master_enabled_false(client: TestClient):
    """POST /automation/stop sets db_master_enabled=false in diagnostics."""
    stop_response = client.post("/api/automation/stop")
    assert stop_response.status_code == 200
    diag_response = client.get("/api/diagnostics")
    assert diag_response.status_code == 200
    data = diag_response.json()
    assert data["db_master_enabled"] is False


def test_start_sets_db_master_enabled_true(client: TestClient):
    """POST /automation/start sets db_master_enabled=true in diagnostics (persisted before engine.start)."""
    with get_db() as db:
        seed_profile(db, "testprofile")
        seed_queue_items(db, 3)
    client.post("/api/automation/start", json={})
    diag_response = client.get("/api/diagnostics")
    assert diag_response.status_code == 200
    data = diag_response.json()
    assert data["db_master_enabled"] is True


def test_start_accepts_no_body(client: TestClient):
    """POST /api/automation/start works with no body (no 422)."""
    with get_db() as db:
        seed_profile(db, "testprofile")
        seed_queue_items(db, 3)
    response = client.post("/api/automation/start")
    assert response.status_code != 422, f"Start must accept no body, got {response.status_code}: {response.text}"


def test_start_accepts_empty_json(client: TestClient):
    """POST /api/automation/start works with {} body."""
    with get_db() as db:
        seed_profile(db, "testprofile")
        seed_queue_items(db, 3)
    response = client.post("/api/automation/start", json={})
    assert response.status_code != 422, f"Start must accept empty JSON, got {response.status_code}: {response.text}"

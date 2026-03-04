"""
TDD: /debug/runtime endpoint (DEV-only, ENGAGEFLOW_DEBUG=1).
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


def test_debug_runtime_404_when_disabled(client):
    """GET /debug/runtime returns 404 when ENGAGEFLOW_DEBUG is not set."""
    import app as app_module
    orig = app_module.ENGAGEFLOW_DEBUG
    app_module.ENGAGEFLOW_DEBUG = False
    try:
        r = client.get("/debug/runtime")
        assert r.status_code == 404
    finally:
        app_module.ENGAGEFLOW_DEBUG = orig


def test_debug_runtime_reports_db_and_newest_activity(client):
    """GET /debug/runtime returns db_path, newest_activity_timestamp when ENGAGEFLOW_DEBUG=1."""
    import app as app_module
    orig = app_module.ENGAGEFLOW_DEBUG
    app_module.ENGAGEFLOW_DEBUG = True
    try:
        with get_db() as db:
            name = seed_profile(db, "testprofile")
            seed_activity_feed(db, name, 2, utc=True)
        r = client.get("/debug/runtime")
        assert r.status_code == 200
        data = r.json()
        assert "db_path" in data
        assert "db_file_exists" in data
        assert "newest_activity_timestamp" in data
        assert "engine_running" in data
        assert "now_utc" in data
    finally:
        app_module.ENGAGEFLOW_DEBUG = orig

"""
TDD: Stop persists masterEnabled=False; startup respects it (no auto-start when disabled).
"""
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import (
    app,
    get_db,
    ensure_tables,
    _load_or_create_automation_settings,
)
from automation.engine import AutomationEngine
from tests.helpers import seed_profile, seed_queue_items


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


def _set_master_enabled_in_db(enabled: bool) -> None:
    """Helper to set masterEnabled in automation_settings."""
    with get_db() as db:
        settings = _load_or_create_automation_settings(db)
        payload = settings.model_dump()
        payload["masterEnabled"] = enabled
        db.execute(
            "INSERT INTO automation_settings (key, value) VALUES ('default', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (json.dumps(payload),),
        )
        db.commit()


async def _mock_start(self, profiles=None, global_settings=None):
    self._state.is_running = True
    return {"success": True, "isRunning": True}


def test_stop_persists_disabled_flag(client):
    """POST /automation/stop sets masterEnabled=False in DB."""
    with get_db() as db:
        seed_profile(db, "testprofile")
        seed_queue_items(db, 3)
    # Ensure masterEnabled is True first
    _set_master_enabled_in_db(True)
    # Start then stop
    with patch.object(AutomationEngine, "start", _mock_start):
        client.post("/automation/start", json={})
    client.post("/automation/stop")
    with get_db() as db:
        settings = _load_or_create_automation_settings(db)
    assert settings.masterEnabled is False


def test_start_enables_flag_and_starts_engine(client):
    """POST /automation/start sets masterEnabled=True in DB."""
    _set_master_enabled_in_db(False)
    with get_db() as db:
        seed_profile(db, "testprofile")
        seed_queue_items(db, 3)
    with patch.object(AutomationEngine, "start", _mock_start):
        client.post("/automation/start", json={})
    with get_db() as db:
        settings = _load_or_create_automation_settings(db)
    assert settings.masterEnabled is True


def test_startup_does_not_autostart_when_flag_disabled():
    """When masterEnabled=False in DB and ENGAGEFLOW_AUTOMATION_ENABLED=1, startup skips auto-start."""
    ensure_tables()
    _set_master_enabled_in_db(False)
    with patch("app.ENGAGEFLOW_AUTOMATION_ENABLED", True):
        with TestClient(app) as client:
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json().get("running") is False

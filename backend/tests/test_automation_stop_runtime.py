"""
TDD: POST /api/automation/stop must never return 500. Idempotent.
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app, ensure_tables


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_stop_api_prefixed_never_500(client):
    """POST /api/automation/stop returns 200 always, never 500."""
    r = client.post("/api/automation/stop")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert "ok" in data or "success" in data
    assert "request_id" in data


def test_stop_api_prefixed_never_500_when_engine_raises_cancelled(client):
    """When engine.stop() raises CancelledError, still return 200 (never 500)."""
    engine = getattr(client.app.state, "automation_engine", None)
    if engine is None:
        pytest.skip("automation_engine not in app.state (lifespan)")

    async def _raise_cancelled(*_args, **_kwargs):
        raise asyncio.CancelledError()

    with patch.object(engine, "stop", side_effect=_raise_cancelled):
        r = client.post("/api/automation/stop")
    assert r.status_code == 200, f"Stop must never 500 when engine raises CancelledError: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("isRunning") is False
    assert data.get("ok") is True


def test_stop_api_prefixed_never_500_when_engine_raises_runtime_error(client):
    """When engine.stop() raises RuntimeError, return 200 with ok=false (never 500)."""
    engine = getattr(client.app.state, "automation_engine", None)
    if engine is None:
        pytest.skip("automation_engine not in app.state (lifespan)")

    async def _raise_runtime(*_args, **_kwargs):
        raise RuntimeError("simulated stop failure")

    async def _status_running(*_args, **_kwargs):
        return {"isRunning": True, "success": True}

    with patch.object(engine, "stop", side_effect=_raise_runtime), patch.object(
        engine, "get_status", side_effect=_status_running
    ):
        r = client.post("/api/automation/stop")
    assert r.status_code == 200, f"Stop must never 500 when engine raises: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is False
    assert "error" in data
    assert data.get("isRunning") is False


def test_stop_api_prefixed_idempotent(client):
    """POST /api/automation/stop twice returns 200 both times."""
    r1 = client.post("/api/automation/stop")
    assert r1.status_code == 200
    r2 = client.post("/api/automation/stop")
    assert r2.status_code == 200
    assert r2.json().get("isRunning") is False

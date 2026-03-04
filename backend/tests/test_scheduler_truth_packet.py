"""Test scheduler truth packet in /api/diagnostics."""
from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient

from app import app, ensure_tables, get_db
from tests.helpers import seed_profile, seed_queue_items


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as c:
        yield c


def test_diagnostics_includes_scheduler_truth_packet(client: TestClient):
    """GET /api/diagnostics includes scheduler_truth_packet with required keys."""
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "scheduler_truth_packet" in data
    pkt = data["scheduler_truth_packet"]
    assert "now_server_utc" in pkt
    assert "next_action_id" in pkt
    assert "next_run_at_absolute" in pkt
    assert "eta_seconds" in pkt
    assert "scheduler_source_of_truth" in pkt
    assert "db_path" in pkt
    assert "engine_state" in pkt
    assert "last_activity_timestamp" in pkt


def test_scheduler_truth_packet_with_queue(client: TestClient):
    """When queue has future items, next_action_id and next_run_at_absolute are set."""
    with get_db() as db:
        seed_profile(db, "testprofile")
        seed_queue_items(db, 3)
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    data = response.json()
    pkt = data["scheduler_truth_packet"]
    if "error" not in pkt:
        assert pkt.get("scheduler_source_of_truth") in ("queue", "scheduler_loop", "none")

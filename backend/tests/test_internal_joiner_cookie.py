"""
TDD: /internal/joiner/profiles/{id}/cookie — secret-gated, never logs cookie contents.
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app import app, get_db, ensure_tables


@pytest.fixture
def client_with_secret():
    """Client with ENGAGEFLOW_JOINER_SECRET set."""
    os.environ["ENGAGEFLOW_JOINER_SECRET"] = "test-secret-12345"
    try:
        ensure_tables()
        with TestClient(app) as client:
            yield client
    finally:
        os.environ.pop("ENGAGEFLOW_JOINER_SECRET", None)


@pytest.fixture
def profile_id_with_cookie(client_with_secret):
    """Create profile with cookie_json, return id."""
    pid = str(uuid.uuid4())
    with get_db() as db:
        pc = {str(r["name"]) for r in db.execute("PRAGMA table_info(profiles)").fetchall()}
        if "cookie_json" not in pc:
            db.execute("ALTER TABLE profiles ADD COLUMN cookie_json TEXT")
            db.commit()
        db.execute(
            """INSERT INTO profiles (id, name, username, password, email, proxy, avatar, status, dailyUsage, groupsConnected, cookie_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pid, "test@example.com", "test", "", "test@example.com", "", "", "active", 0, 0, '[{"name":"auth_token","value":"x"}]'),
        )
        db.commit()
    return pid


def test_internal_joiner_cookie_missing_header_401(client_with_secret, profile_id_with_cookie):
    """Missing X-JOINER-SECRET header -> 401."""
    r = client_with_secret.get(f"/internal/joiner/profiles/{profile_id_with_cookie}/cookie")
    assert r.status_code == 401


def test_internal_joiner_cookie_wrong_secret_401(client_with_secret, profile_id_with_cookie):
    """Wrong X-JOINER-SECRET -> 401."""
    r = client_with_secret.get(
        f"/internal/joiner/profiles/{profile_id_with_cookie}/cookie",
        headers={"X-JOINER-SECRET": "wrong-secret"},
    )
    assert r.status_code == 401


def test_internal_joiner_cookie_correct_secret_200(client_with_secret, profile_id_with_cookie):
    """Correct X-JOINER-SECRET -> 200, cookie_json in response (never in logs)."""
    r = client_with_secret.get(
        f"/internal/joiner/profiles/{profile_id_with_cookie}/cookie",
        headers={"X-JOINER-SECRET": "test-secret-12345"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "cookie_json" in data
    assert data["cookie_json"] is not None
    assert len(data["cookie_json"]) > 0


def test_internal_joiner_cookie_profile_not_found_404(client_with_secret):
    """Non-existent profile -> 404."""
    r = client_with_secret.get(
        "/internal/joiner/profiles/00000000-0000-0000-0000-000000000000/cookie",
        headers={"X-JOINER-SECRET": "test-secret-12345"},
    )
    assert r.status_code == 404


def test_internal_joiner_cookie_no_secret_env_401():
    """When ENGAGEFLOW_JOINER_SECRET not set, any request -> 401."""
    os.environ.pop("ENGAGEFLOW_JOINER_SECRET", None)
    pid = str(uuid.uuid4())
    ensure_tables()
    with get_db() as db:
        pc = {str(r["name"]) for r in db.execute("PRAGMA table_info(profiles)").fetchall()}
        if "cookie_json" not in pc:
            db.execute("ALTER TABLE profiles ADD COLUMN cookie_json TEXT")
            db.commit()
        db.execute(
            """INSERT INTO profiles (id, name, username, password, email, proxy, avatar, status, dailyUsage, groupsConnected)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pid, "x", "x", "", "", "", "", "active", 0, 0),
        )
        db.commit()
    with TestClient(app) as client:
        r = client.get(
            f"/internal/joiner/profiles/{pid}/cookie",
            headers={"X-JOINER-SECRET": "anything"},
        )
    assert r.status_code == 401

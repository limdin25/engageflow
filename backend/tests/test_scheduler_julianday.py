"""
TDD: Scheduler must use julianday() for queue datetime comparison.
Bug: String comparison (scheduledFor > ?) fails when formats differ (space vs T, no Z vs Z).
Fix: Use julianday(scheduledFor) > julianday(?) for robust comparison.
"""
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient

from app import app, ensure_tables, get_db
from tests.helpers import seed_profile


@pytest.fixture
def client():
    ensure_tables()
    with TestClient(app) as client:
        yield client


def test_julianday_finds_future_item_with_space_format(client):
    """Julianday() correctly finds future queue items when scheduledFor uses space format.
    String comparison (scheduledFor > ?) fails: '2026-03-04 12:05:00' < '2026-03-04T12:00:00Z' (space < T)."""
    now_utc = datetime.now(timezone.utc)
    future = now_utc + timedelta(minutes=5)
    scheduled_str = future.strftime("%Y-%m-%d %H:%M:%S")
    now_iso = now_utc.isoformat(timespec="seconds").replace("+00:00", "Z")

    with get_db() as db:
        name = seed_profile(db, "julianday_diag")
        db.execute(
            """INSERT INTO queue_items (id, profile, profileId, community, communityId, postId, keyword, keywordId, scheduledTime, scheduledFor, priorityScore, countdown)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), name, "pid2", "comm", "cid", "post2", "kw", "kid", scheduled_str, scheduled_str, 50, 180),
        )
        db.commit()

        # String comparison excludes space format (proves bug)
        row_str = db.execute(
            "SELECT id FROM queue_items WHERE scheduledFor > ? ORDER BY scheduledFor ASC LIMIT 1", (now_iso,)
        ).fetchone()
        assert row_str is None, "String comparison must exclude space format"

        # Julianday finds it (proves fix)
        row_jd = db.execute(
            "SELECT id FROM queue_items WHERE julianday(scheduledFor) > julianday(?) ORDER BY julianday(scheduledFor) ASC LIMIT 1",
            (now_iso,),
        ).fetchone()
        assert row_jd is not None, "Julianday must find future item"

        db.execute("DELETE FROM queue_items WHERE profileId = ?", ("pid2",))
        db.execute("DELETE FROM profiles WHERE name = ?", (name,))
        db.commit()

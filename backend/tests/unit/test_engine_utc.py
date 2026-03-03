"""Unit test: engine uses timezone.utc for activity timestamps."""
from pathlib import Path


def test_engine_activity_timestamps_use_utc():
    """Engine must use datetime.now(timezone.utc) for activity_rows timestamp."""
    engine_path = Path(__file__).resolve().parent.parent.parent / "automation" / "engine.py"
    text = engine_path.read_text()
    assert "timezone.utc" in text, "engine.py must use timezone.utc for activity timestamps"
    assert "datetime.now(timezone.utc)" in text or "datetime.now(timezone.utc).isoformat()" in text, (
        "engine must use datetime.now(timezone.utc).isoformat() for activity timestamps"
    )

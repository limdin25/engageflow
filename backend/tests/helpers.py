"""Test helpers for seeding DB."""
import uuid
from datetime import datetime, timezone, timedelta


def seed_queue_items(db, n: int):
    for i in range(n):
        t = (datetime.now() + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%S")
        db.execute(
            """INSERT INTO queue_items (id, profile, profileId, community, communityId, postId, keyword, keywordId, scheduledTime, scheduledFor, priorityScore, countdown)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), f"profile{i % 2}", f"pid-{i % 2}", "comm", "cid", f"post{i}", "kw", "kid", t, t, 50, 60),
        )
    db.commit()


def seed_activity_feed(db, profile_name: str, n: int, *, utc: bool = True):
    base = datetime.now(timezone.utc) if utc else datetime.now()
    if utc:
        fmt = lambda i: (base + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    else:
        fmt = lambda i: (base + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%S")
    for i in range(n):
        db.execute(
            """INSERT INTO activity_feed (id, profile, groupName, action, timestamp, postUrl)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), profile_name, "group", "Commented", fmt(i), f"https://x.com/p{i}"),
        )
    db.commit()


def seed_profile(db, name: str = "testprofile"):
    db.execute(
        """INSERT OR REPLACE INTO profiles (id, name, username, password, email, proxy, avatar, status, dailyUsage, groupsConnected)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(uuid.uuid4()), name, name, "", "", "", "", "active", 0, 0),
    )
    db.commit()
    return name

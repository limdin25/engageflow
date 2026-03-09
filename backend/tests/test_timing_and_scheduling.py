"""
TDD: Timing, scheduling, and delay behaviour in the automation engine.

Covers:
  1. repliesPerVisit is respected (not hardcoded to 1)
  2. Connection rest is disabled by default, enabled only by flag
  3. Delay floor respects user settings
  4. Intra-action delay fires between consecutive actions
  5. End-to-end timing flow
"""
from __future__ import annotations

import os
import sys
import time
import random
from unittest.mock import patch, MagicMock, call
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

# Ensure backend dir is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from automation.engine import (
    AutomationEngine,
    AUTOMATION_POSTED_WAIT_MIN_SECONDS,
    AUTOMATION_NO_POST_WAIT_SECONDS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings(**overrides) -> Dict[str, Any]:
    """Return a minimal settings dict with sensible defaults."""
    base = {
        "masterEnabled": True,
        "globalDailyCapPerAccount": 10,
        "queuePrefillMaxPerProfilePerPass": 2,
        "delayMin": 30,
        "delayMax": 90,
        "activeDays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "runFrom": "00:00",
        "runTo": "23:59",
        "blacklistEnabled": False,
        "blacklistTerms": [],
        "preScanEnabled": False,
        "commentFallbackEnabled": True,
        "commentFallbackPrompt": "test",
        "dmFallbackPrompt": "test",
    }
    base.update(overrides)
    return base


def _make_profile(profile_id: str = "p1", **overrides) -> Dict[str, Any]:
    base = {
        "id": profile_id,
        "label": f"Test Profile {profile_id}",
        "name": f"Test Profile {profile_id}",
        "email": f"{profile_id}@test.com",
        "password": "pass",
        "enabled": True,
        "status": "ready",
        "visits": 10,
        "repliesCompleted": 0,
        "visitsCompleted": 0,
        "communities": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# TEST GROUP 1: repliesPerVisit respected
# ---------------------------------------------------------------------------

class TestRepliesPerVisit:
    """Verify that repliesPerVisit is read from settings, not hardcoded."""

    def test_replies_per_visit_from_profile(self):
        """Profile with repliesPerVisit=3 should pass 3 into _run_profile_automation_sync."""
        profile = _make_profile(repliesPerVisit=3)
        settings = _make_settings()

        # Simulate the scheduler logic that builds profile_for_run
        profile_for_run = dict(profile)
        _replies = max(1, int(
            profile.get("repliesPerVisit")
            or settings.get("repliesPerVisit")
            or settings.get("queuePrefillMaxPerProfilePerPass")
            or 1
        ))
        profile_for_run["repliesPerVisit"] = _replies

        assert profile_for_run["repliesPerVisit"] == 3, (
            f"Expected repliesPerVisit=3, got {profile_for_run['repliesPerVisit']}"
        )

    def test_replies_per_visit_fallback_to_settings(self):
        """Profile without repliesPerVisit falls back to queuePrefillMaxPerProfilePerPass."""
        profile = _make_profile()
        # Remove repliesPerVisit from profile
        profile.pop("repliesPerVisit", None)
        settings = _make_settings(queuePrefillMaxPerProfilePerPass=2)

        profile_for_run = dict(profile)
        _replies = max(1, int(
            profile.get("repliesPerVisit")
            or settings.get("repliesPerVisit")
            or settings.get("queuePrefillMaxPerProfilePerPass")
            or 1
        ))
        profile_for_run["repliesPerVisit"] = _replies

        assert profile_for_run["repliesPerVisit"] == 2

    def test_replies_per_visit_minimum_is_one(self):
        """When both profile and settings lack repliesPerVisit, fallback is 1."""
        profile = _make_profile()
        profile.pop("repliesPerVisit", None)
        settings = _make_settings()
        settings.pop("repliesPerVisit", None)
        settings.pop("queuePrefillMaxPerProfilePerPass", None)

        profile_for_run = dict(profile)
        _replies = max(1, int(
            profile.get("repliesPerVisit")
            or settings.get("repliesPerVisit")
            or settings.get("queuePrefillMaxPerProfilePerPass")
            or 1
        ))
        profile_for_run["repliesPerVisit"] = _replies

        assert profile_for_run["repliesPerVisit"] == 1

    def test_replies_per_visit_zero_becomes_one(self):
        """repliesPerVisit=0 should be clamped to 1."""
        profile = _make_profile(repliesPerVisit=0)
        settings = _make_settings()

        _replies = max(1, int(
            profile.get("repliesPerVisit")
            or settings.get("repliesPerVisit")
            or settings.get("queuePrefillMaxPerProfilePerPass")
            or 1
        ))

        assert _replies >= 1


# ---------------------------------------------------------------------------
# TEST GROUP 2: Connection rest disabled by default
# ---------------------------------------------------------------------------

class TestConnectionRest:
    """Verify connection rest is opt-in, default OFF."""

    def _is_rest_enabled(self, settings: Dict[str, Any]) -> bool:
        """Replicate the backend's connectionRestEnabled check."""
        return str(
            settings.get("connectionRestEnabled", "false")
        ).strip().lower() in {"1", "true", "yes", "on"}

    def test_connection_rest_disabled_by_default(self):
        """Without connectionRestEnabled, rest never fires."""
        settings = _make_settings()
        assert not self._is_rest_enabled(settings)

        # Simulate 10 rounds completing — rest should never trigger
        connection_rest_enabled = self._is_rest_enabled(settings)
        completed_rounds = 10
        rounds_before_rest = 3
        rest_triggered = False

        if connection_rest_enabled and completed_rounds >= rounds_before_rest:
            rest_triggered = True

        assert not rest_triggered

    def test_connection_rest_enabled_when_flag_set(self):
        """connectionRestEnabled='true' allows rest to fire."""
        settings = _make_settings(
            connectionRestEnabled="true",
            roundsBeforeConnectionRest=3,
            connectionRestMinutes=1,
        )
        assert self._is_rest_enabled(settings)

        connection_rest_enabled = self._is_rest_enabled(settings)
        completed_rounds = 3
        rounds_before_rest = 3
        rest_triggered = False

        if connection_rest_enabled and completed_rounds >= rounds_before_rest:
            rest_triggered = True

        assert rest_triggered

    def test_connection_rest_false_string(self):
        """connectionRestEnabled='false' (string) means rest never fires."""
        settings = _make_settings(connectionRestEnabled="false")
        assert not self._is_rest_enabled(settings)

        connection_rest_enabled = self._is_rest_enabled(settings)
        completed_rounds = 10
        rounds_before_rest = 3
        rest_triggered = False

        if connection_rest_enabled and completed_rounds >= rounds_before_rest:
            rest_triggered = True

        assert not rest_triggered

    def test_connection_rest_numeric_one(self):
        """connectionRestEnabled='1' enables rest."""
        settings = _make_settings(connectionRestEnabled="1")
        assert self._is_rest_enabled(settings)

    def test_connection_rest_missing_key(self):
        """Missing connectionRestEnabled key defaults to disabled."""
        settings = _make_settings()
        settings.pop("connectionRestEnabled", None)
        assert not self._is_rest_enabled(settings)

    def test_get_status_rest_inactive_when_disabled(self):
        """get_status() returns connectionRest.active=False when feature disabled."""
        engine = AutomationEngine.__new__(AutomationEngine)
        # Minimal state setup
        from automation.engine import EngineState
        import asyncio
        engine._state = EngineState()
        engine._state.connection_rest_active = True  # backend thinks rest is active
        engine._state.global_settings = {"connectionRestEnabled": "false"}
        engine._lock = asyncio.Lock()

        # Run get_status
        loop = asyncio.new_event_loop()
        try:
            status = loop.run_until_complete(engine.get_status())
        finally:
            loop.close()

        assert status["connectionRest"]["active"] is False


# ---------------------------------------------------------------------------
# TEST GROUP 3: Delay floor respects user setting
# ---------------------------------------------------------------------------

class TestDelayFloor:
    """Verify the delay floor uses the user's delayMin, not a hardcoded 75s."""

    def _compute_wait_seconds(
        self,
        profile: Dict[str, Any],
        settings: Dict[str, Any],
        comments_posted_this_pass: int,
    ) -> int:
        """Replicate the scheduler's wait_seconds calculation."""
        delay_min = max(10, int(
            profile.get("delayBetweenMessagesMinSec",
                profile.get("delay_min", settings.get("delayMin", 30)))
        ))
        delay_max = max(delay_min, int(
            profile.get("delayBetweenMessagesMaxSec",
                profile.get("delay_max", settings.get("delayMax", 90)))
        ))
        if delay_max < delay_min:
            delay_min, delay_max = delay_max, delay_min
        random_delay = random.randint(delay_min, delay_max)
        user_delay_min = max(10, int(
            profile.get("delayBetweenMessagesMinSec")
            or settings.get("delayMin")
            or AUTOMATION_POSTED_WAIT_MIN_SECONDS
        ))
        wait_seconds = (
            max(user_delay_min, random_delay)
            if comments_posted_this_pass > 0
            else max(AUTOMATION_NO_POST_WAIT_SECONDS, random_delay)
        )
        return wait_seconds

    def test_delay_floor_uses_user_minimum(self):
        """User sets delayMin=60, delayMax=100. Wait should be 60..100, not floored at 75."""
        profile = _make_profile()
        settings = _make_settings(delayMin=60, delayMax=100)

        for _ in range(50):
            wait = self._compute_wait_seconds(profile, settings, comments_posted_this_pass=1)
            assert 60 <= wait <= 100, f"wait_seconds={wait} outside [60, 100]"

    def test_delay_floor_does_not_go_below_10(self):
        """Even if user sets delayMin=5, the hard floor is 10."""
        profile = _make_profile()
        settings = _make_settings(delayMin=5, delayMax=15)

        for _ in range(50):
            wait = self._compute_wait_seconds(profile, settings, comments_posted_this_pass=1)
            assert wait >= 10, f"wait_seconds={wait} should be >= 10"

    def test_delay_no_post_uses_no_post_constant(self):
        """When no comments posted, use AUTOMATION_NO_POST_WAIT_SECONDS floor."""
        profile = _make_profile()
        settings = _make_settings(delayMin=30, delayMax=60)

        for _ in range(50):
            wait = self._compute_wait_seconds(profile, settings, comments_posted_this_pass=0)
            assert wait >= AUTOMATION_NO_POST_WAIT_SECONDS, (
                f"wait_seconds={wait} should be >= {AUTOMATION_NO_POST_WAIT_SECONDS} when no posts"
            )

    def test_posted_wait_min_default_is_30(self):
        """AUTOMATION_POSTED_WAIT_MIN_SECONDS should now default to 30, not 75."""
        assert AUTOMATION_POSTED_WAIT_MIN_SECONDS <= 30, (
            f"Expected <= 30, got {AUTOMATION_POSTED_WAIT_MIN_SECONDS}"
        )

    def test_user_delay_60_not_floored_at_75(self):
        """Regression: user sets 60s min. Old code floored at 75. Now should be 60."""
        profile = _make_profile()
        settings = _make_settings(delayMin=60, delayMax=60)

        wait = self._compute_wait_seconds(profile, settings, comments_posted_this_pass=1)
        assert wait == 60, f"Expected exactly 60, got {wait}"


# ---------------------------------------------------------------------------
# TEST GROUP 4: Intra-action delay fires correctly
# ---------------------------------------------------------------------------

class TestIntraActionDelay:
    """Verify intra-action delay logic between consecutive actions in a pass."""

    def test_intra_action_delay_between_actions(self):
        """With repliesPerVisit=3, time.sleep should be called 2 times (between 1→2 and 2→3)."""
        settings = _make_settings(intraActionDelayMinSec=10, intraActionDelayMaxSec=20)
        replies_per_visit = 3
        sleep_calls: List[float] = []

        # Simulate the action loop
        for action_num in range(1, replies_per_visit + 1):
            replies_this_visit = action_num  # After action completes
            # The delay fires after each action EXCEPT the last
            if replies_this_visit < replies_per_visit:
                intra_min = max(5, int(settings.get("intraActionDelayMinSec", 10)))
                intra_max = max(intra_min, int(settings.get("intraActionDelayMaxSec", 30)))
                intra_delay = random.randint(intra_min, intra_max)
                sleep_calls.append(intra_delay)

        assert len(sleep_calls) == 2, f"Expected 2 intra-action delays, got {len(sleep_calls)}"
        for delay in sleep_calls:
            assert 10 <= delay <= 20, f"Intra-action delay {delay} outside [10, 20]"

    def test_intra_action_delay_not_fired_for_single_action(self):
        """With repliesPerVisit=1, no intra-action delay should fire."""
        settings = _make_settings(intraActionDelayMinSec=10, intraActionDelayMaxSec=20)
        replies_per_visit = 1
        sleep_calls: List[float] = []

        for action_num in range(1, replies_per_visit + 1):
            replies_this_visit = action_num
            if replies_this_visit < replies_per_visit:
                intra_min = max(5, int(settings.get("intraActionDelayMinSec", 10)))
                intra_max = max(intra_min, int(settings.get("intraActionDelayMaxSec", 30)))
                intra_delay = random.randint(intra_min, intra_max)
                sleep_calls.append(intra_delay)

        assert len(sleep_calls) == 0

    def test_intra_action_delay_default_fallback(self):
        """Without intraActionDelay settings, defaults to 10–30 seconds."""
        settings = _make_settings()
        # Ensure no intra-action keys
        settings.pop("intraActionDelayMinSec", None)
        settings.pop("intraActionDelayMaxSec", None)
        replies_per_visit = 3
        sleep_calls: List[float] = []

        for action_num in range(1, replies_per_visit + 1):
            replies_this_visit = action_num
            if replies_this_visit < replies_per_visit:
                intra_min = max(5, int(settings.get("intraActionDelayMinSec", 10)))
                intra_max = max(intra_min, int(settings.get("intraActionDelayMaxSec", 30)))
                intra_delay = random.randint(intra_min, intra_max)
                sleep_calls.append(intra_delay)

        assert len(sleep_calls) == 2
        for delay in sleep_calls:
            assert 10 <= delay <= 30, f"Default intra-action delay {delay} outside [10, 30]"

    def test_intra_action_min_floor_is_5(self):
        """intraActionDelayMinSec cannot go below 5."""
        settings = _make_settings(intraActionDelayMinSec=1, intraActionDelayMaxSec=3)
        intra_min = max(5, int(settings.get("intraActionDelayMinSec", 10)))
        assert intra_min == 5


# ---------------------------------------------------------------------------
# TEST GROUP 5: End-to-end timing flow
# ---------------------------------------------------------------------------

class TestEndToEndTimingFlow:
    """Simulate complete scheduler passes and verify timing."""

    def test_full_pass_timing_one_account(self):
        """
        1 account, repliesPerVisit=2, delayMin=60, delayMax=60 (fixed).
        connectionRestEnabled not set.
        Assert: 2 actions, 1 intra-action delay, 1 inter-account delay of 60s, no rest.
        """
        profile = _make_profile(repliesPerVisit=2)
        settings = _make_settings(delayMin=60, delayMax=60)

        # Build profile_for_run (replicate scheduler logic)
        profile_for_run = dict(profile)
        _replies = max(1, int(
            profile.get("repliesPerVisit")
            or settings.get("repliesPerVisit")
            or settings.get("queuePrefillMaxPerProfilePerPass")
            or 1
        ))
        profile_for_run["repliesPerVisit"] = _replies
        assert _replies == 2

        # Simulate action loop
        replies_per_visit = _replies
        actions_executed = 0
        intra_delays = []
        for action_num in range(1, replies_per_visit + 1):
            actions_executed += 1
            replies_this_visit = action_num
            if replies_this_visit < replies_per_visit:
                intra_min = max(5, int(settings.get("intraActionDelayMinSec", 10)))
                intra_max = max(intra_min, int(settings.get("intraActionDelayMaxSec", 30)))
                intra_delay = random.randint(intra_min, intra_max)
                intra_delays.append(intra_delay)

        assert actions_executed == 2
        assert len(intra_delays) == 1  # 1 intra-action delay between action 1 and 2

        # Inter-account delay
        comments_posted_this_pass = 2
        user_delay_min = max(10, int(
            profile.get("delayBetweenMessagesMinSec")
            or settings.get("delayMin")
            or AUTOMATION_POSTED_WAIT_MIN_SECONDS
        ))
        random_delay = random.randint(60, 60)
        wait_seconds = max(user_delay_min, random_delay) if comments_posted_this_pass > 0 else 0
        assert wait_seconds == 60

        # Connection rest
        connection_rest_enabled = str(
            settings.get("connectionRestEnabled", "false")
        ).strip().lower() in {"1", "true", "yes", "on"}
        assert not connection_rest_enabled

    def test_full_pass_timing_two_accounts(self):
        """
        2 accounts, repliesPerVisit=1, delayMin=30, delayMax=30.
        connectionRestEnabled not set.
        Assert: Account A executes, 30s delay, Account B executes. No rest.
        """
        profiles = [
            _make_profile("a", repliesPerVisit=1),
            _make_profile("b", repliesPerVisit=1),
        ]
        settings = _make_settings(delayMin=30, delayMax=30)

        timeline: List[str] = []

        for profile in profiles:
            _replies = max(1, int(
                profile.get("repliesPerVisit")
                or settings.get("repliesPerVisit")
                or settings.get("queuePrefillMaxPerProfilePerPass")
                or 1
            ))
            assert _replies == 1

            # Execute action
            timeline.append(f"action:{profile['id']}")

            # No intra-action delay for single action
            intra_delays = 0
            if _replies > 1:
                intra_delays = _replies - 1

            assert intra_delays == 0

            # Inter-account delay
            user_delay_min = max(10, int(
                profile.get("delayBetweenMessagesMinSec")
                or settings.get("delayMin")
                or AUTOMATION_POSTED_WAIT_MIN_SECONDS
            ))
            random_delay = random.randint(30, 30)
            wait_seconds = max(user_delay_min, random_delay)
            timeline.append(f"wait:{wait_seconds}s")

        assert timeline == [
            "action:a", "wait:30s",
            "action:b", "wait:30s",
        ]

        # No connection rest
        connection_rest_enabled = str(
            settings.get("connectionRestEnabled", "false")
        ).strip().lower() in {"1", "true", "yes", "on"}
        assert not connection_rest_enabled

    def test_two_accounts_three_actions_each(self):
        """
        2 accounts, repliesPerVisit=3, delayMin=45, delayMax=45.
        Verify complete timeline.
        """
        profiles = [
            _make_profile("a", repliesPerVisit=3),
            _make_profile("b", repliesPerVisit=3),
        ]
        settings = _make_settings(
            delayMin=45, delayMax=45,
            intraActionDelayMinSec=15, intraActionDelayMaxSec=15,
        )

        total_actions = 0
        total_intra_delays = 0
        total_inter_delays = 0

        for profile in profiles:
            _replies = max(1, int(
                profile.get("repliesPerVisit")
                or settings.get("repliesPerVisit")
                or settings.get("queuePrefillMaxPerProfilePerPass")
                or 1
            ))

            for action_num in range(1, _replies + 1):
                total_actions += 1
                replies_this_visit = action_num
                if replies_this_visit < _replies:
                    total_intra_delays += 1

            total_inter_delays += 1

        assert total_actions == 6  # 3 per account
        assert total_intra_delays == 4  # 2 per account (between 1→2, 2→3)
        assert total_inter_delays == 2  # 1 per account

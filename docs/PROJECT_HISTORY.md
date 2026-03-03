# PROJECT HISTORY — Append Only Log

## Entry Format

Each entry must include:

Date:
Change:
Files:
Tests:
Verification:
Reversal: (must be copy-paste executable command, or "IRREVERSIBLE — [reason]" if undo not possible)
ReversalTested: Yes | No
Risk Level: LOW | MEDIUM | HIGH | SECURITY

**Reversal rules:**
- Write the exact command to undo the change (e.g. `git revert abc1234 --no-edit`).
- Test the reversal before marking complete when possible.
- If the change cannot be undone, mark as IRREVERSIBLE and document mitigation.

Risk Level is mandatory for changes affecting:

- Authentication
- Execution layer
- WebSockets
- External APIs
- Secrets
- Configuration

Legacy entries using pipe format remain valid, but all future entries must follow structured format above.

---

## Entry #1

Date: 2026-03-02
Change: Governance initialized (Genesis v2)
Files:

- docs/DISCIPLINE.md
- docs/PROJECT_STATE.md
- docs/PROJECT_HISTORY.md

Tests: None
Verification: Confirm docs exist
Reversal: `rm -rf docs/`
ReversalTested: No
Risk Level: LOW

---

## Entry #2

Date: 2026-03-02
Change: PROJECT_HISTORY — added executable Reversal format, ReversalTested field
Files:

- docs/PROJECT_HISTORY.md

Tests: None
Verification: Confirm new format and rules present
Reversal: `git revert HEAD -- docs/PROJECT_HISTORY.md` (after committing this change)
ReversalTested: No
Risk Level: LOW

---

## Entry #3

Date: 2026-03-03
Change: GitHub bootstrap — initialized git repo, pushed to https://github.com/limdin25/engageflow
Files:

- .gitignore (added backend/.env)
- All backend, frontend, docs, scripts

Tests: None
Verification: Repo accessible, main branch pushed
Reversal: `git remote remove origin`
ReversalTested: No
Risk Level: LOW

---

## Entry #4

Date: 2026-03-03
Change: Audit fixes — profile rotation, auth timing, activity feed name, log buffering
Files:

- backend/app.py
- backend/automation/engine.py

Tests: None (manual verification)
Verification: See checklist in PR #1

**A Problem**

- Inbox sync stuck on single profile; auth check failed before DOM ready; activity timeline empty (profile name mismatch); log writes dropped on SQLite lock.

**B Hypotheses**

- profile_last_attempt not updated on error; blind wait insufficient for SPA hydration; activity_feed used profileLabel vs profiles.name; lock contention caused silent log drops.

**C Proof**

- Code audit: profile_last_attempt set after fetch; wait_for_timeout(1800/900) before marker check; profile_label fallback in _persist_activity_rows; _insert_backend_log returns on locked.

**D Acceptance Criteria**

- 2+ profiles rotate across sync; no wait_for_timeout in auth paths; activity_feed.profile = profiles.name; buffered logs flush after sync.

**E Plan**

- Move profile_last_attempt to top of loop; replace with wait_for_selector; use canonical name for activity_feed; add _LOG_BUFFER and _flush_log_buffer.

**F Diffs**

- app.py: profile_last_attempt repositioned, _goto_skool_entry_page wait_for_selector, _LOG_BUFFER, _flush_log_buffer, activity_feed profile resolve.
- engine.py: validate_session wait_for_selector, _persist_activity_rows profile_for_feed.

**G Tests**

- None automated.

**H Test Plan**

- Manual: run sync with 2+ profiles; check /connect or login check; run automation; query activity_feed; verify buffer flush.

**I Rollback**

- `git revert a105328 --no-edit`

**J Success Metric**

- Profile rotation works; auth validation succeeds; activity timeline populated; no skipped log warnings under load.

Reversal: `git revert a105328 --no-edit`
ReversalTested: No
Risk Level: MEDIUM (execution layer, DB writes)

---

## Entry #5

Date: 2026-03-03
Change: 8 surgical audit fixes (dev branch) — deadlock prevention, log buffer ts/key/requeue, profile_for_feed fallback, backfill resolution, docker-compose.dev volume
Files:

- backend/app.py
- backend/automation/engine.py
- docker-compose.dev.yml
- docker-compose.yml

Tests: None (manual verification)
Verification: Sync lock releases; buffered logs show creation ts; Buffered message; activity_feed edge cases; backfill resolves profile; dev volume mount; log order preserved.

Reversal: `git revert <commit> --no-edit`
ReversalTested: No
Risk Level: MEDIUM (DB, sync lock)

---

## Entry #6

Date: 2026-03-03
Change: Deploy queue/activity fixes via TDD [TD-124] — queue limit=30, activity limit=100, engine UTC timestamps
Files:

- backend/app.py (read_queue limit, read_activity limit)
- backend/automation/engine.py (datetime.now(timezone.utc).isoformat())
- backend/tests/test_queue_limit.py
- backend/tests/test_activity_timeline.py
- backend/tests/unit/test_engine_utc.py
- backend/tests/helpers.py
- backend/tests/conftest.py
- backend/requirements.txt (pytest, httpx)

Tests: pytest backend/tests/ -v (5 passed), pytest backend/tests/unit/ -v --maxfail=1 (1 passed)
Verification: GET /queue returns ≤30, GET /activity returns ≤100, activity timestamps UTC
Reversal: `git revert HEAD --no-edit`
ReversalTested: No
Risk Level: LOW

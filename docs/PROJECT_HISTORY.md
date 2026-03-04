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
Reversal: IRREVERSIBLE — deletes all governance docs with no local recovery.
Mitigation: GitHub retains history. To restore: git checkout <commit> -- docs/
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
Reversal: IRREVERSIBLE — remote push to GitHub cannot be undone via CLI.
git remote remove origin only disconnects local remote; GitHub repo retains all history.
Mitigation: repo deletion requires manual GitHub admin action.
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

Reversal: `git revert ea52715 --no-edit`
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

---

## Entry #7 — Governance correction (main→dev)

Date: 2026-03-03
Change: Fix was pushed to main; governance requires dev-first. Cherry-picked ab6c7e6 onto dev, resolved conflicts.
Files: backend/app.py, frontend (api, DashboardPage), docs
Commit: 8e58c34 (Fix dashboard queue/timeline + add backend tests (dev))
Verification: dev pushed; DEV VPS deploy manual (ssh root@72.61.147.80)
Reversal: `git revert 8e58c34 --no-edit`
ReversalTested: No
Risk Level: LOW

---

## Entry #8 — TDD coverage: queue interleaving + timeline ordering

Date: 2026-03-03
Change: Added backend tests for queue limit=30, profile interleaving (Robinhood rule), activity newest-first.
Files: backend/tests/test_dashboard_queue_timeline.py
Tests: pytest backend/tests/test_dashboard_queue_timeline.py -v (5 passed)
Verification: test_queue_returns_at_most_30, test_queue_interleaves_profiles, test_queue_api_interleaves, test_activity_newest_first, test_activity_api_newest_first
Commit: 8e58c34 (included in Entry #7)
Reversal: `git revert 8e58c34 --no-edit`
ReversalTested: No
Risk Level: LOW

---

## Entry #9 — Dashboard reliability: auto-refresh + guarantee signal

Date: 2026-03-03
Change: Activity Timeline and Action Queue auto-update every 10s; refetch on window focus. Added "Last updated: Xs ago" and "No new activity detected in last N min" when newest activity &gt; 10 min. Fixed stray conflict marker in DashboardPage.
Files: frontend/src/hooks/useEngageFlow.ts, frontend/src/pages/DashboardPage.tsx, backend/tests/test_dashboard_queue_timeline.py
Tests: pytest backend/tests/ -v (14 passed). Added test_activity_endpoint_orders_desc_and_limits, test_queue_endpoint_returns_30_and_interleaves.
Verification: Activity/queue refetch every 10s; refetchOnWindowFocus: true; guarantee signal when no new activity.
Reversal: `git revert HEAD --no-edit`
ReversalTested: No
Risk Level: LOW

---

## Entry #10 — Railway DEV automation: ENGAGEFLOW_AUTOMATION_ENABLED + /health

Date: 2026-03-04
Change: Make Railway DEV backend run automation so health.running=true. Added ENGAGEFLOW_AUTOMATION_ENABLED (default OFF), GET /health with running=engine.is_running, lifespan auto-start when enabled and DB writable. TDD tests for health and activity.
Files:
- backend/app.py (ENGAGEFLOW_AUTOMATION_ENABLED, _is_db_writable, lifespan auto-start, GET /health)
- backend/tests/test_health_automation.py (test_health_running_false_when_disabled, test_health_running_true_when_scheduler_started, test_activity_updates_when_action_executes)
- docs/PROJECT_STATE.md
- docs/PROJECT_HISTORY.md

Tests: pytest backend/tests -v --maxfail=1 (17 passed)
Verification: curl https://engageflow-dev.up.railway.app/health after setting ENGAGEFLOW_AUTOMATION_ENABLED=1
Reversal: `git revert HEAD --no-edit`
ReversalTested: No
Risk Level: LOW

---

## Entry #11 — Activity Timeline display: interleave + dedupe (UI-only)

Date: 2026-03-04
Commit: fc2ab4e
Change: Activity Timeline display: dedupe exact duplicates (by id or profile+groupName+action+timestamp), interleave by profile (round-robin), preserve per-profile order. No long runs of same email; no duplicate rows. N=30 for initial display.
Files:
- frontend/src/lib/activityTimeline.ts (dedupeActivities, interleaveByProfile)
- frontend/src/lib/activityTimeline.test.ts (TDD)
- frontend/src/pages/DashboardPage.tsx (use processedActivity = interleaveByProfile(dedupeActivities(filteredActivity)))

Tests: npm test (5 passed), npm run build (success)
Verification: https://selfless-renewal-dev.up.railway.app — Activity Timeline interleaved, no duplicates
Reversal: `git revert HEAD --no-edit`
ReversalTested: No
Risk Level: LOW

---

## Entry #12 — Activity Timeline "19 hr ago" root cause + timestamp normalization

Date: 2026-03-04
Change: Root cause: DB mismatch — Railway DEV backend reads Railway DB; automation not running there (or runs on VPS with different DB). Fix: configure Railway DEV to run automation (ENGAGEFLOW_AUTOMATION_ENABLED=1, ENGAGEFLOW_DB_PATH, OpenAI key). Defensive: backend _normalize_activity_timestamp now appends Z to ISO timestamps without timezone for frontend parseISO.
Files:
- backend/app.py (_normalize_activity_timestamp)
- backend/tests/test_activity_timestamp.py (test_activity_timestamp_normalized_with_z_suffix)
- docs/PROJECT_STATE.md
- docs/PROJECT_HISTORY.md

Tests: pytest backend/tests -v (18 passed)
Verification: curl https://engageflow-dev.up.railway.app/activity?limit=1 — timestamps end with Z
Reversal: `git revert HEAD --no-edit`
ReversalTested: No
Risk Level: LOW

---

## Entry #13 — /debug/runtime + canonical DEV pairing (H1 proved)

Date: 2026-03-04
Change: Proved H1 (ENV/DB mismatch): Railway DEV and VPS return different activity IDs. Added GET /debug/runtime (ENGAGEFLOW_DEBUG=1) for db_path, engine_running, newest_activity_timestamp, newest_queue_scheduledFor. Documented canonical DEV pairing: Option A Railway, Option B VPS.
Files:
- backend/app.py (ENGAGEFLOW_DEBUG, /debug/runtime)
- backend/tests/test_debug_runtime.py
- docs/PROJECT_STATE.md
- docs/PROJECT_HISTORY.md

Tests: pytest backend/tests -v (20 passed)
Verification: ENGAGEFLOW_DEBUG=1 and curl /debug/runtime
Reversal: `git revert HEAD --no-edit`
ReversalTested: No
Risk Level: LOW

---

## Entry #14 — Canonical DEV to Railway + frontend determinism

Date: 2026-03-04
Change: Canonicalized DEV to Railway as single source of truth. Frontend: require VITE_BACKEND_URL when deployed (no fallback probing); use only VITE_BACKEND_URL when set. VPS automation to be disabled manually after Railway proves healthy.
Files:
- frontend/src/lib/api.ts (require VITE_BACKEND_URL when non-localhost; no fallback when env set)
- frontend/src/lib/api.test.ts (TDD: use VITE_BACKEND_URL when set; throw when deployed without it)
- docs/PROJECT_STATE.md (canonical DEV = Railway, exact vars, verification curls)
- docs/PROJECT_HISTORY.md

Tests: npm test (7 passed), pytest backend/tests (20 passed), npm run build (success)
Verification: Set Railway vars per PROJECT_STATE.md; curl /health, /debug/runtime, /activity; disable VPS automation after Railway running:true.
Reversal: `git revert HEAD --no-edit`
ReversalTested: No
Risk Level: LOW

---

## Entry #15 — DISCIPLINE: always push to origin dev

Date: 2026-03-04
Change: Added mandatory step: after every meaningful change, commit and push to origin dev. GitHub dev = source of truth; Railway DEV auto-deploys from dev branch.
Files: docs/DISCIPLINE.md
Tests: None
Verification: Section 0 item 4 and Section 9 now require push to origin dev.
Reversal: `git revert HEAD --no-edit`
ReversalTested: No
Risk Level: LOW

---

## Entry #16 — Governance correction: MD audit fixes

Date: 2026-03-04
Change: Fix 5 governance errors found in audit:
  (1) PROJECT_STATE.md default branch label corrected to dev
  (2) Duplicate Next Actions item #4 renumbered
  (3) Railway Frontend/Backend URLs split and labelled in GitHub section
  (4) PROJECT_HISTORY.md Entry #1 rm -rf reversal replaced with IRREVERSIBLE
  (5) Entry #3 git remote remove origin marked IRREVERSIBLE
  (6) Entry #5 unfilled SHA resolved (ea52715)
Files:
  - docs/PROJECT_STATE.md
  - docs/PROJECT_HISTORY.md
Tests: None (docs only)
Verification: git diff HEAD~1 docs/ matches only lines above
Reversal: `git revert HEAD --no-edit && git push origin dev`
ReversalTested: No
Risk Level: LOW

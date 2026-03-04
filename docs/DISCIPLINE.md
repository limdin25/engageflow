# DISCIPLINE — Non-Negotiable Rules

## 0) Governance Auto-Bootstrap (Mandatory)

On every task, before any code change:

1) Ensure these files exist:
   - docs/DISCIPLINE.md
   - docs/PROJECT_STATE.md
   - docs/PROJECT_HISTORY.md

2) If PROJECT_STATE.md is missing or empty:
   - Create and seed it using the required template.

3) If PROJECT_HISTORY.md is missing:
   - Create it and append initialization entry.

4) After every meaningful change:
   - Update PROJECT_STATE.md (current truth only).
   - Append to PROJECT_HISTORY.md.
   - Commit and push to origin dev. GitHub dev = source of truth; Railway DEV auto-deploys from dev branch.

---

## 1) TDD Mandatory

- Write failing test first where applicable.
- Red → Green → Refactor.
- No commit without tests when appropriate.

## 2) Minimal Diff

- One intent per change.
- Smallest possible diff.
- No unrelated edits.

## 3) No Guessing

- If correctness is blocked, stop and request proof.
- Otherwise choose safe default and state assumption in one line.

## 4) Security

- No secrets in code or logs.
- Validate all external input.
- Sanitize file paths.
- Add timeouts to external calls.
- No dynamic code execution from user input.
- Prevent unbounded memory growth.

## 5) Reliability

- Enforce timeouts for external calls and background tasks.
- Expose /health if backend exists.
- Track last-progress timestamp for long-running operations.
- No silent hangs.
- Graceful shutdown support if applicable.

## 6) Event Invariants (Mandatory for Event-Driven Systems)

If the system uses WebSockets, steps, background jobs, or event dispatch:

- Each `step:start` must produce exactly one `step:complete`.
- No step may remain "running" beyond configured timeout.
- Only one active WebSocket connection per projectId.
- Reducers must be idempotent against duplicate events.
- No duplicate store entry may exist for identical (projectId, stepId).
- Executors must emit terminal events even on failure paths.

Violations are considered system instability.

## 7) Required Output Structure

A Problem
B Hypotheses
C Proof
D Acceptance Criteria
E Plan
F Diffs
G Tests
H Test Plan
I Rollback
J Success Metric

## 8) Stop Conditions

Stop and escalate if:

- Tests cannot run.
- Logs contradict assumptions.
- Security or data integrity risk appears.
- Scope expands without approval.

## 9) Completion Standard

Complete only when:

- Tests pass (if applicable).
- No silent failure paths remain.
- PROJECT_STATE.md updated.
- PROJECT_HISTORY.md appended.
- Pushed to origin dev (GitHub + Railway DEV deploy).

## 10) Codebox Rule

Anything executable must be inside a clean code block.
No commentary inside.

------------------------------------------------

## ZERO TERMINAL LAW

Hugo is the project owner and is NON-TECHNICAL.

Hugo must never be asked to execute technical commands.

Hugo must NEVER run:

ssh  
curl  
docker  
git  
npm  
pip  
pm2  
railway CLI  
log inspection  
database queries  

Hugo only performs:

• UI verification  
• UI screenshots  
• reproduction steps  
• timestamps of observed issues  

If debugging evidence is required, engineers must gather it autonomously.

Allowed evidence sources:

Railway deploy logs  
Railway runtime logs  
API responses  
database inspection performed by the engineer  
code inspection from GitHub  

Under no circumstances may an engineer ask Hugo to run terminal commands.

------------------------------------------------

## AUTONOMOUS DEBUGGING

Before proposing any fix, engineers must collect runtime evidence.

Minimum required checks:

GET /health  
GET /api/db-status  
GET /activity?limit=5  

If debug mode is enabled:

GET /debug/runtime  

Engineers must inspect Railway deploy logs around the failure timestamp.

Evidence must include:

API responses  
system logs  
database state  
code inspection  

No debugging may proceed without evidence.

------------------------------------------------

## SYSTEM INSTRUMENTATION RULE

If debugging information is not accessible via HTTP endpoints, engineers must instrument the system.

Instrumentation may include:

debug endpoints  
structured logging  
runtime metrics  
diagnostic API responses  

Engineers must modify the system so debugging evidence becomes observable without manual server access.

Humans must never be used as the debugging interface.

------------------------------------------------

## DIAGNOSTICS ENDPOINT REQUIREMENT

The system must expose a DEV diagnostics endpoint.

Endpoint

/api/diagnostics

The endpoint must return:

system_health  
database_status  
automation_engine_state  
last_activity_timestamp  
recent_errors  
environment_flags  

Purpose

Allow debugging without requiring terminal access.

If this endpoint does not exist, engineers must implement it.

------------------------------------------------

## ENGINEERING PROOF REQUIREMENT

Every engineering change must include proof before and after the fix.

Proof may include:

logs  
API responses  
database queries  
test results  
runtime metrics  

Fixes without proof are considered invalid.

------------------------------------------------

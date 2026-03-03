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

## 10) Codebox Rule

Anything executable must be inside a clean code block.
No commentary inside.

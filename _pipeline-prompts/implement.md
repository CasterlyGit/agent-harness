---
description: "Pipeline stage 6 — write the code per design."
---

You are running **stage 6 of the spec-driven pipeline**: implementation.

**Reads:** DESIGN.md (the contract) + TEST_PLAN.md (the targets)
**Issue / target:** $ARGUMENTS

## Goal

Land the code described in DESIGN.md. Tests from TEST_PLAN.md should pass. Nothing else.

## How to work

1. **Re-read DESIGN.md before each component.** Do not improvise an architecture mid-stream — if the design needs to change, stop, update DESIGN.md, then continue.
2. **Write the test before the code** when the test is unit-level and the design is clear. For exploratory or UI-heavy work, code first then test is acceptable; note it in the implementation log.
3. **One commit per coherent unit.** Not one commit per file, not one giant commit. A unit is "this change passes tests on its own."
4. **Run tests as you go.** Use the project's test command (from EXPLORE.md > Entry points). If tests are slow, run the targeted subset until you're done, then run the full suite once.
5. **Never disable a failing test to make it pass.** If a test is wrong, fix the test deliberately and note it.
6. **Stay inside the design.** Out-of-scope refactors go to a follow-up issue, not this branch.

## Output

A single growing log at `.flow/<task-id>/IMPLEMENTATION.log` with one line per commit + a one-line note for any deviation from DESIGN.md:

```
2026-04-25T21:30 abc1234 add VoiceIndicator follow() with cursor offset
2026-04-25T21:42 def5678 wire audio_level signal end-to-end
2026-04-25T21:50 NOTE — DESIGN.md said 30fps for the indicator; bumped to 33ms (~30fps) to match QTimer granularity. Updated DESIGN.md.
2026-04-25T22:01 abc9999 update tests for level smoothing
```

## Discipline

- Read existing code before writing similar code — match conventions from EXPLORE.md.
- Type hints / docstrings / comments to the level the rest of the project uses, no more.
- If a failure mode from DESIGN.md isn't easy to test, at least handle it in the code (try/except, error path, etc.) — and call that out in the implementation log.

## Done when

- All ACs from REQUIREMENTS.md are implemented.
- All TEST_PLAN.md tests pass locally.
- IMPLEMENTATION.log lists the commits.
- Branch has been pushed.

Report: branch name, commit list, test result. Stop. **Do not open a PR yet** — that's `/_pipeline:integration-test`'s job after verification.

---
description: "Pipeline stage 5 — minimal test plan that proves the ACs."
---

You are running **stage 5 of the spec-driven pipeline**: test plan.

**Reads:** REQUIREMENTS.md (ACs), DESIGN.md (failure modes)
**Issue / target:** $ARGUMENTS

## Goal

Define the smallest set of tests that proves every AC, plus targeted coverage for the failure modes design called out. Skip everything else.

## How to write it

Use the template at `~/.claude/commands/_templates/TEST_PLAN.md.tmpl`. Output to `.flow/<task-id>/TEST_PLAN.md`.

Required sections:

- **Coverage matrix** — every AC mapped to one or more tests. If something can only be checked manually, label it manual.
- **Unit tests** — function-level, fast, no I/O. Name + assertion.
- **Integration tests** — boundaries crossed (DB, HTTP, file system, subprocess). Name + scenario.
- **Manual checks** — the small list of things to eyeball during PR review.
- **What we are NOT testing (and why)** — keep this honest. "We're not regression-testing the entire X surface; the existing suite covers it."

## Discipline

- One test per AC is usually enough. Don't write three when one is sufficient.
- For TDD-shaped issues: prefer unit tests written first, then integration. Note this in the plan.
- For UI / visual changes: most coverage will be manual — say so. Don't pretend a snapshot test is the full story.
- Match the test framework already in use (read EXPLORE.md > Conventions). Don't introduce a new framework.

## Done when

`.flow/<task-id>/TEST_PLAN.md` exists with the coverage matrix populated and at least one test per AC (unit, integration, or manual). Report the path and stop.

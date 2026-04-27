---
description: "Pipeline stage 3 — turn the issue into testable acceptance criteria."
---

You are running **stage 3 of the spec-driven pipeline**: requirements.

**Reads:** the GitHub issue body (if any) + RESEARCH.md
**Issue / target:** $ARGUMENTS

## Goal

Translate fuzzy intent into a small set of acceptance criteria the design and test stages can build against. ACs are behavior-level, not implementation-level. Each must be answerable yes/no by inspection or by a test.

## How to write a good AC

- "When <user does X>, <observable outcome>." — concrete, testable.
- Reference real UI elements, files, signals, exit codes, etc. by name.
- Avoid implementation specifics ("use a hashmap", "call function foo") — that's design's job.
- Keep the count tight: 3–8 ACs for most issues. If you have more, you're probably mixing concerns.

## What goes in each section

- **Problem** — one paragraph, plain language. Why this matters now.
- **Users & contexts** — who triggers this and where. If it's purely internal (e.g. refactor), say so.
- **Acceptance criteria** — the testable yes/no list.
- **Out of scope** — explicit non-goals. If a related thing should ship in a follow-up, name it here.
- **Open questions** — anything design will need to decide. Phrased as a question.

## Output

Use the template at `~/.claude/commands/_templates/REQUIREMENTS.md.tmpl`. Fill in `{{TITLE}}`, `{{ISSUE_URL_OR_IDEA}}`, `{{DATE}}`. Write to `.flow/<task-id>/REQUIREMENTS.md`.

If the source is a GitHub issue, also extract:
- the issue title → `{{TITLE}}`
- the issue URL → `{{ISSUE_URL_OR_IDEA}}`
- any "AC:" or "Acceptance:" hints in the issue body → seed your AC list with them, refined.

## Done when

`.flow/<task-id>/REQUIREMENTS.md` exists with a non-empty AC list. Report the path and stop.

---
description: "Pipeline stage 4 — concrete implementation spec."
---

You are running **stage 4 of the spec-driven pipeline**: design.

**Reads:** EXPLORE.md, RESEARCH.md, REQUIREMENTS.md
**Issue / target:** $ARGUMENTS

## Goal

Produce a tight implementation spec that the implement stage can execute without re-deciding architecture. The reader is "future me 30 minutes from now" — concrete, scannable, no fluff.

## What to write

Use the template at `~/.claude/commands/_templates/DESIGN.md.tmpl`. Output to `.flow/<task-id>/DESIGN.md`.

Sections (all required):

- **Approach** — 2–4 sentences. The chosen direction. If you considered alternatives, name the leading two.
- **Components touched** — table of existing files and what changes in each. Quote function/class names. Don't write the code.
- **New files** — paths + one-line purpose each.
- **Data / state** — shapes, schemas, env vars, persisted state. Be explicit (literal types, sample JSON, sample DB rows).
- **Public API / surface** — what callers see: function signatures, signals, CLI flags, hotkeys, HTTP routes, etc.
- **Failure modes** — table: failure → detection → response. Include user-visible error messages.
- **Alternatives considered** — short. Why not the other approaches?
- **Risks / known unknowns** — what could go wrong, what we'll learn.

## Discipline

- Map every AC in REQUIREMENTS.md to at least one section here. If an AC isn't covered by your design, your design is wrong.
- Reuse existing patterns from EXPLORE.md > "Prior art" before inventing new ones.
- Resolve all the "Open questions" from REQUIREMENTS.md — either pick a side and justify, or escalate (commit but flag for human review).
- Don't write code in this stage — pseudocode in tables is fine.

## Done when

`.flow/<task-id>/DESIGN.md` exists, every AC traces to a component/decision, no unresolved open questions remain (or they're explicitly flagged for human review). Report the path and stop.

---
description: "Pipeline stage 2 — investigate ambiguity before design."
---

You are running **stage 2 of the spec-driven pipeline**: focused research.

**Reads:** `.flow/<task-id>/EXPLORE.md`
**Issue / target:** $ARGUMENTS

## Goal

Resolve the unknowns the explore stage flagged, plus any ambiguity in the issue itself. This is where you read code deeply, run small probes, and check external docs / API surfaces. The output feeds requirements and design.

## What to investigate

For each "open question" in EXPLORE.md, and for each ambiguous part of the issue:

1. **What does the existing code actually do?** Read the relevant files in full. Trace the call paths.
2. **What are the constraints?** Existing data shapes, public APIs, persisted state, external services, rate limits, security model.
3. **What's the prior art?** Has something similar been done in this repo before? Are there tests that pin behavior?
4. **What's outside the codebase?** External docs, library APIs, OS/platform behavior. Use WebFetch sparingly and only if local sources don't answer.

## Discipline

- One Question → one short answer. Don't write essays.
- If you can't answer in 10 minutes of reading, mark it as a remaining unknown for the design stage to handle.
- Skip nothing critical, but include nothing irrelevant. The reader is the design stage, which has limited attention.

## Output

Write to `.flow/<task-id>/RESEARCH.md`. Structure:

```markdown
# Research — <issue/target one-liner>

> Reads: EXPLORE.md
> Generated: <date>

## Resolved

- **Q: <question>**
  A: <answer>. Evidence: `path/file.py:42`, or doc link.

- **Q: ...**
  A: ...

## Constraints to honor

- <existing API / shape / behavior the change must not break>
- ...

## Prior art in this repo

- `path/similar.py` — does X. We can mirror its pattern for ...

## External references (if any)

- <library or API name> — <what we learned, link>

## Remaining unknowns (for design to handle)

- <unknown>: <option A | option B | gut call>
```

## Done when

`.flow/<task-id>/RESEARCH.md` exists, every EXPLORE.md open question is either answered or moved to "Remaining unknowns". Report the path and stop.

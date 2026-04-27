---
description: "Pipeline stage 1 — map the existing repo before any design work."
---

You are running **stage 1 of the spec-driven pipeline**: codebase exploration.

**Input:** the current working directory (an existing repo).
**Issue / target:** $ARGUMENTS

## Goal

Build a working mental model of this repo so later stages don't waste time. Output is a single short artifact, not a tour.

## What to find

1. **Stack** — language, framework, package manager, runtime versions. Look at the obvious manifest first (package.json / pyproject.toml / Cargo.toml / go.mod / requirements.txt).
2. **Layout** — top-level directories and their roles. One sentence each.
3. **Entry points** — what runs the app, what the test command is, what the build is.
4. **Conventions** — naming, file structure, formatting, lint config, type-checking, test framework. Quote two or three concrete examples (file paths) rather than guessing.
5. **Recent activity** — last 5 commits, current branch, any uncommitted changes.
6. **Targeted scan** — for the specific issue/target above, list the 3–10 files most likely to need changes. Don't read them deeply yet — that's research's job.

## Discipline

- Use Glob + Grep + a small number of Reads. **Don't read everything.**
- If a file is huge, sample its top 50 lines and search for the symbols you care about.
- Skip vendored dirs (`node_modules`, `.venv`, `dist`, `build`).
- 5-minute time budget. If you're still wandering after that, write what you have.

## Output

Write to `.flow/<task-id>/EXPLORE.md` in the repo root. `<task-id>` is `init` for new projects, or `issue-<N>` when targeting a GitHub issue.

Use this structure:

```markdown
# Explore — <repo name>

## Stack
- ...

## Layout
- `src/` — ...
- `tests/` — ...

## Entry points
- run: `<command>`
- test: `<command>`
- build: `<command>`

## Conventions
- ...

## Recent activity
- branch: `<name>`
- last commits:
  - `<sha>` <subject>
- uncommitted: <yes/no, brief>

## Files relevant to this target
- `path/x.py` — <one-line reason>
- `path/y.py` — ...

## Open questions for the next stage
- ...
```

Commit the artifact only — no source changes in this stage.

## Done when

`.flow/<task-id>/EXPLORE.md` exists and the "Files relevant to this target" list is non-empty (or explicitly explains why nothing existing is relevant — e.g. greenfield). Report the path and stop.

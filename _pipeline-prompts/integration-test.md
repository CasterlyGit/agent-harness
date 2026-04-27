---
description: "Pipeline stage 7 — verify ACs end-to-end, then open the PR."
---

You are running **stage 7 of the spec-driven pipeline**: integration & PR.

**Reads:** REQUIREMENTS.md (ACs), TEST_PLAN.md, IMPLEMENTATION.log
**Issue / target:** $ARGUMENTS

## Goal

Prove that what shipped actually meets the acceptance criteria, then surface it for human review.

## What to do

1. **Run the full test suite.** Not just the targeted tests from implementation. Confirm green.
2. **Walk every AC.** For each AC in REQUIREMENTS.md:
   - If covered by an automated test → cite the test name + file path.
   - If manual → execute the manual check; record what you saw.
   - If failed → file as "Outstanding issue" and decide ready-with-caveats or not-ready.
3. **Walk every failure mode** in DESIGN.md and confirm the handling exists in code.
4. **Write the integration report** using `~/.claude/commands/_templates/INTEGRATION.md.tmpl` to `.flow/<task-id>/INTEGRATION.md`.
5. **Commit `.flow/<task-id>/`** so all artifacts are visible in the PR.
6. **Open the PR** linking the source issue (if any):
   - Title: `<short imperative summary>` (use the issue title if greenfield).
   - Body: a 1–3 line summary, then a bullet list of ACs with ✅ / ⚠️ / ❌, then a "Test plan" section pointing at TEST_PLAN.md.
   - Use `gh pr create` with `--fill` overridden by the body above.
   - Move the GitHub Project card (if any) to "In Review".

## Discipline

- Don't fix bugs in this stage. If you find one, log it as Outstanding and let the human decide if it blocks the PR or becomes a follow-up issue.
- Don't pad the PR body. The reader is the human reviewer; they want to know "does it meet the ACs, and what do I look at first."
- Push artifacts (`.flow/`) on the same branch — they live in the PR diff for review.

## Done when

- INTEGRATION.md decision is one of `✅`, `⚠️`, or `❌`.
- The PR exists. Print the URL.
- Stop.

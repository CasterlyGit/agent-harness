---
description: "Decompose a big ticket into N internal steps, run them in chain on ONE branch, open ONE PR with all the work for the user to test. Wall-clock ~20-40 min total. Use when /iterate-fast halts saying 'too big to split'."
---

You are running **`/epic`** — the chained-decomposition skill for big tickets.

**Args:** `$ARGUMENTS` — either an inbox markdown path, a GitHub issue URL, or `owner/repo#N`.

This is the right skill when one ticket is too big for `/iterate-fast` (multi-subsystem work, >8 min coding) but the user doesn't want to manage N small PRs. You decompose internally, commit step by step on one branch, and present **one PR** when the whole epic is done.

The user only sees the result — they don't approve the step plan, don't review intermediate work, don't merge between steps. They test the integrated app at the end.

---

## Hard contracts

1. **One branch, one PR.** All step commits land on `auto/<issue>-<slug>`. Open the PR only after the last step succeeds.
2. **Steps are real units of code.** Each step = 1-3 commits, scoped to one subsystem (auth, API client, UI surface, etc.). Not "design", not "research" — implementation slices.
3. **Plan is written, not just thought.** Save the decomposition to `.epic/issue-<num>/plan.md` before starting. This is the checkpoint if something fails.
4. **Halt on first failure.** If step K fails (build red, tests fail, can't reconcile with step K-1's output) — stop, report, don't auto-retry. The user will look.
5. **Progress is visible.** After each step, write `progress.step / progress.total / progress.label / progress.updated_at` to `inbox/.state.json` so the status row shows live advancement.
6. **No new GitHub issues.** Internal steps are not tickets. The single original issue stays as the unit; the PR closes it on merge.

---

## Steps

### 1. Resolve the input

Same as `/iterate-fast`:
- inbox path → read the file, repo is the parent of `inbox/`
- GitHub URL → `gh issue view`
- `owner/repo#N` → split, `gh issue view N --repo owner/repo`

Capture: `REPO_PATH`, `OWNER_REPO`, `ISSUE_NUM`, `TITLE`, `BODY`, `INBOX_FILE` (if applicable).

### 2. File the issue if inbox-only

If the inbox file has no `gh_issue:` line yet, file it:

```bash
gh issue create --repo "$OWNER_REPO" --title "$TITLE" --body "$BODY" --label "epic"
```

Add `<!-- gh_issue: <num> -->` to the inbox file so it's not double-filed.

### 3. Decompose into a step plan

Read the ticket carefully. Identify:
- The subsystems involved (auth, transport, UI, data layer, etc.)
- The natural dependency chain between them
- Where the integration points are

Write a plan with **3-7 steps**. Each step:
- Has a 4-8 word title (`Auth flow scaffolding`, `API client + types`, `Library screen`)
- Has a 1-2 sentence "what we'll do" body
- Lists the files / modules it'll touch
- States what verification will look like (specific test, build green, or "no observable change yet, integration verified at step K")

Save the plan to `$REPO_PATH/.epic/issue-${ISSUE_NUM}/plan.md` like:

```markdown
# Epic plan: <title>
Issue: #${ISSUE_NUM}

## Step 1 — <title>
What: <body>
Touches: <files/modules>
Verify: <how>

## Step 2 — <title>
...
```

Commit the plan as the **first commit** on the branch:

```
chore(epic): plan #<N> — <title>
```

If decomposition isn't possible (the work is genuinely atomic, or you can't see clean seams), **halt**. Comment on the issue: "this isn't actually multi-step, run with /iterate-fast instead." Exit.

### 4. Set up the branch

```bash
cd "$REPO_PATH"
git fetch origin
EXISTING=$(git branch --list "auto/${ISSUE_NUM}-*" --format "%(refname:short)" | head -1)
if [ -n "$EXISTING" ]; then
  BRANCH="$EXISTING"
  git checkout "$BRANCH"
else
  SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-' | sed 's/--*/-/g; s/^-//; s/-$//' | cut -c1-40)
  BRANCH="auto/${ISSUE_NUM}-${SLUG}"
  git checkout -b "$BRANCH" main
fi
```

Commit the plan from step 3 now (it's already written, just `git add .epic && git commit`).

### 5. Run each step

For step K of N:

a) **Write progress to state.json.** If `INBOX_STATE_FILE` and `INBOX_TICKET_KEY` env vars are set (the wrapper passes them), tick:

```bash
NOW=$(date '+%Y-%m-%dT%H:%M:%S')
TMP=$(mktemp)
jq --arg k "$INBOX_TICKET_KEY" --argjson s $K --argjson t $N --arg lbl "<step title>" --arg u "$NOW" \
   '.[$k].progress = {step: $s, total: $t, label: $lbl, updated_at: $u}' \
   "$INBOX_STATE_FILE" > "$TMP" && mv "$TMP" "$INBOX_STATE_FILE"
```

b) **Implement the step.** Read the source you'll edit, write the code, follow the existing patterns. One coherent commit (or 2-3 closely related ones) per step. Subjects:

```
<type>(<scope>): <step description> — epic #<N> step <K>/<total>
```

c) **Verify in-place.** Run targeted tests, build the project. If anything's red, **halt** — don't proceed to step K+1 on a broken base. Drop a comment on the issue with what failed and at which step.

d) Move to step K+1.

### 6. Open the PR

After the last step lands cleanly:

```bash
git push -u origin "$BRANCH"

gh pr create --repo "$OWNER_REPO" \
  --title "$TITLE" \
  --body "$(cat <<EOF
Closes #${ISSUE_NUM}.

## Epic decomposition

This PR was assembled by \`/epic\` from $N internal steps. Each step is a separate commit you can review independently:

<bulleted list: step K — sha — subject>

## Plan

See \`.epic/issue-${ISSUE_NUM}/plan.md\` (committed as the first commit on this branch).

## Verification

<what builds, what tests pass, what was integration-verified at the final step>

🤖 Assembled via /epic
EOF
)" \
  --base main --head "$BRANCH"
```

### 7. Final state.json + report

Tick progress one last time:

```bash
jq --arg k "$INBOX_TICKET_KEY" --argjson s $N --argjson t $N --arg u "$NOW" \
   '.[$k].progress = {step: $s, total: $t, label: "PR opened", updated_at: $u}' ...
```

Print to stdout: issue, branch, plan path, all step commits, PR URL, "Done — ready for user testing." Stop.

---

## When to halt

| Situation | Action |
|---|---|
| Ticket is genuinely atomic (no clean decomposition) | Comment "use /iterate-fast" on the issue. Exit. |
| Step K's build/test fails | Comment with step K, what failed, where to resume. Exit. Don't retry. |
| Step K can't be implemented because step K-1 produced something unexpected | Same — pause, comment, exit. The user will look. |
| Step plan would have >8 steps | Reconsider — this is too big even for /epic. Comment, ask user to scope down. |
| Required dependency missing (`gh`, branch can't be created) | Tell the user. Exit. |

---

## After the PR is open

This skill is **done** when the PR is open with all step commits. The user tests the integrated app, reviews the commits in PR order, and merges (or runs `/pr-amend` if they want changes).

Do **not** auto-merge. Do **not** start follow-up tickets. The user closes the loop.

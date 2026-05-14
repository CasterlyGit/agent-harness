---
description: "Bring an existing GitHub repo into the workflow: clone locally, create a Project, sync labels + columns, install issue templates, link existing issues."
---

You are running **`/onboard`**.

**Args:** $ARGUMENTS  → `<owner>/<repo>` (e.g. `CasterlyGit/curby`).

## What to do

Run all steps. Report what changed; skip steps where nothing was needed.

### 1. Local clone

```bash
LOCAL=~/Documents/Dev/<repo-slug>
[ -d "$LOCAL/.git" ] || gh repo clone <owner>/<repo> "$LOCAL"
```

`<repo-slug>` is just the repo name (the part after `/`).

### 2. Create the Project (if missing)

```bash
EXISTING=$(gh project list --owner @me --format json --jq '.projects[] | select(.title=="<repo>") | .number')
if [ -z "$EXISTING" ]; then
  PROJECT_NUM=$(gh project create --owner @me --title "<repo>" --format json --jq .number)
else
  PROJECT_NUM="$EXISTING"
fi
```

Link the repo to the project so issues from this repo show up there:

```bash
gh project link <num> --owner @me --repo <owner>/<repo>
```

### 3. Run `/board-setup` on the project

Invoke the `board-setup` skill with `<num>` as args. This applies Status options + adds Priority + Target fields.

### 4. Run `/label-sync` on the repo

Invoke the `label-sync` skill with `<owner>/<repo>`. This makes labels consistent.

### 5. Drop issue templates (if missing)

```bash
mkdir -p "$LOCAL/.github/ISSUE_TEMPLATE"
[ -f "$LOCAL/.github/ISSUE_TEMPLATE/bug.yml" ] || \
  cp ~/.claude/commands/_templates/ISSUE_BUG.yml "$LOCAL/.github/ISSUE_TEMPLATE/bug.yml"
[ -f "$LOCAL/.github/ISSUE_TEMPLATE/feature.yml" ] || \
  cp ~/.claude/commands/_templates/ISSUE_FEATURE.yml "$LOCAL/.github/ISSUE_TEMPLATE/feature.yml"
```

If files were added, commit + push from a fresh branch:

```bash
cd "$LOCAL"
git switch -c chore/onboard-issue-templates 2>/dev/null || git switch chore/onboard-issue-templates
git add .github/
git commit -m "chore: add issue templates from workspace kit" || true
git push -u origin chore/onboard-issue-templates 2>/dev/null || true
gh pr create --title "chore: add issue templates" --body "Standard issue templates from the workspace kit." --label chore || true
git switch main
```

If nothing was added, skip the branch entirely.

### 6. Install board-sync workflow

Drop the standard board-sync workflow so PR/issue events auto-update the Workspace project Status.

```bash
mkdir -p "$LOCAL/.github/workflows"
[ -f "$LOCAL/.github/workflows/board-sync.yml" ] || \
  cp ~/Documents/Dev/workspace-tools/skills/_board-sync-workflow.yml "$LOCAL/.github/workflows/board-sync.yml"
```

If added, commit + push (same chore branch if you opened one in step 5, otherwise straight to main):

```bash
cd "$LOCAL"
git add .github/workflows/board-sync.yml
git commit -m "Add board-sync workflow — auto-update Workspace project Status on PR/issue events"
git push
```

Remind the user once per onboarding (in the final summary) that the workflow needs a `PROJECT_TOKEN` repo secret — a fine-grained PAT with Projects: Read/Write, Issues: Read, Pull requests: Read. Without it the workflow silently no-ops. Setup URL: `https://github.com/<owner>/<repo>/settings/secrets/actions/new`.

### 7. Backfill existing issues into the project

```bash
gh issue list --repo <owner>/<repo> --state open --json url --jq '.[].url' | while read URL; do
  gh project item-add <num> --owner @me --url "$URL"
done
```

### 8. Print summary

```
Onboarded <owner>/<repo>:
  Local:    ~/Documents/Dev/<repo-slug>
  Project:  https://github.com/users/<owner>/projects/<num>
  Labels:   created N, updated M
  Board:    Status options applied, Priority + Target fields added
  Issues:   <count> existing issues added to project
  Templates: bug.yml + feature.yml (PR #<n> opened) | already present
```

Errors don't stop the flow — log them in the summary and keep going.

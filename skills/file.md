---
description: "File a GitHub issue fast. Sensible defaults, ends up on the right project board automatically."
---

You are running **`/file`**.

**Args:** $ARGUMENTS  → free-form. Examples:
- `bug curby — voice indicator hides under menu bar`
- `feature curby — system-prompt user-environment context for agents`
- `polish — auto-dismiss timing too aggressive`        ← uses cwd's repo
- `chore curby p2 — clean up _archive/`

## Parse

Pick out:
- **type** — first word if it's `bug` / `feature` / `polish` / `chore` / `docs` / `security`. Default `feature`.
- **repo** — second word if it matches a known repo (owner can be inferred from `gh repo view <name> --json owner`). If absent, use cwd's git remote.
- **priority** — anywhere in args, `p0` / `p1` / `p2` / `p3`. Default no priority.
- **title** — the rest after the dash `—` or `--`, or the rest of the string.

If you can't infer the repo, ask once.

## File it

```bash
gh issue create \
  --repo <owner>/<repo> \
  --title "<title>" \
  --body "Filed via /file. <args verbatim>" \
  --label "<type>" \
  ${PRIORITY:+--label "priority:$PRIORITY"}
```

Capture the issue URL.

## Add to project

If the repo has been onboarded (i.e. there's a Project with the same name as the repo), add the issue:

```bash
PROJECT_NUM=$(gh project list --owner @me --format json --jq ".projects[] | select(.title==\"<repo>\") | .number")
[ -n "$PROJECT_NUM" ] && gh project item-add "$PROJECT_NUM" --owner @me --url "<issue-url>"
```

Also add to the hub AND set Status=Backlog + Priority on the card so it actually shows up in a column (not in the "no-status" bucket):

```bash
HUB_NUM=$(gh project list --owner @me --format json --jq '.projects[] | select(.title=="Workspace") | .number')
if [ -n "$HUB_NUM" ]; then
  # Add the issue to the hub project and capture the item id
  ITEM_ID=$(gh project item-add "$HUB_NUM" --owner @me --url "<issue-url>" --format json --jq .id)

  # Resolve project/field/option IDs
  PROJECT_ID=$(gh project view "$HUB_NUM" --owner @me --format json --jq .id)
  STATUS_FIELD_ID=$(gh project field-list "$HUB_NUM" --owner @me --format json --jq '.fields[] | select(.name=="Status") | .id')
  STATUS_BACKLOG_ID=$(gh project field-list "$HUB_NUM" --owner @me --format json --jq '.fields[] | select(.name=="Status") | .options[] | select(.name=="Backlog") | .id')
  PRIORITY_FIELD_ID=$(gh project field-list "$HUB_NUM" --owner @me --format json --jq '.fields[] | select(.name=="Priority") | .id')

  # Set Status=Backlog
  gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
    --field-id "$STATUS_FIELD_ID" --single-select-option-id "$STATUS_BACKLOG_ID"

  # Set Priority — map parsed priority (defaults to P2)
  PRI_NAME=$(echo "${PRIORITY:-p2}" | tr '[:lower:]' '[:upper:]')
  PRI_OPT_ID=$(gh project field-list "$HUB_NUM" --owner @me --format json --jq ".fields[] | select(.name==\"Priority\") | .options[] | select(.name==\"$PRI_NAME\") | .id")
  [ -n "$PRI_OPT_ID" ] && gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
    --field-id "$PRIORITY_FIELD_ID" --single-select-option-id "$PRI_OPT_ID"
fi
```

## Report

```
✅ Filed <owner>/<repo>#<n>
   Title:   <title>
   Type:    <type>   Priority: <p2|none>
   URL:     <issue-url>
   Project: <repo project URL>  (Backlog)
   Hub:     <hub project URL>
```

## When to invoke

- After voice notes, screenshots, or random observations.
- When `/iterate` finds out-of-scope work.
- Mid-debugging when you spot something unrelated.

Stay terse. Don't over-template the body — one line of context is plenty; the title carries the meaning.

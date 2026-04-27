# workspace-tools

Personal agentic-development workflow: write tickets in Obsidian, click a button, watch a Claude Code skill ship a PR. Each project's GitHub repo is the data layer; an Obsidian vault is the dashboard; Claude Code skills are the workers.

## What's in here

```
skills/         Claude Code slash commands (markdown prompts)
  pr-amend.md       — read latest PR comment, implement delta, run tests, push, reply
  iterate-fast.md   — file inbox ticket as issue, branch, code, test, push, open PR
  file.md           — quick GitHub issue filer
  automate.md       — greenfield: idea → new repo + project + initial commit
  onboard.md        — pull an existing repo into the workflow
  hub.md            — bootstrap the master "Workspace" project board
  board-setup.md    — apply standard Status/Priority/Target fields to a Project v2
  label-sync.md     — apply standard label kit to a repo
  iterate.md        — legacy: shells out to the Python orchestrator
  ticket.md         — drop a ticket into the Obsidian Specs watcher
  epic.md           — split a big ticket into N sub-steps, ship one PR
  _templates/*      — issue templates
  _board-kit.json   — Project v2 field config
  _labels.json      — standard label kit

bin/            Shell scripts that hold it together
  inbox-process.sh        — renders ~/<vault>/_status.md from each repo's inbox/.state.json
  inbox-watcher.sh        — fswatch loop: re-renders status on any inbox/ change
  run-skill-with-state.sh — wraps a skill run, writes amending/iterating flags before/after
  progress-tick.sh        — called from inside skills to emit step/total/label progress
  sync-vault.sh           — symlinks each repo's inbox/ into the Obsidian vault
  pr-test.sh              — fresh-checkout test runner for a PR
  run-app.sh              — launch a project's app for manual testing

workspace_tools/   Legacy Python orchestrator (kept around; superseded by skills/)
```

## How it fits together

```
  ┌──────────────────┐
  │ Obsidian vault   │  user writes a ticket in inbox/<slug>.md, sees the
  │  _status.md      │  status dashboard, clicks action buttons
  └────────┬─────────┘
           │ fswatch on inbox/ → bin/inbox-watcher.sh → bin/inbox-process.sh
           ▼
  ┌──────────────────┐
  │ inbox-process.sh │  renders _status.md from each repo's inbox/.state.json
  │                  │  emits .command launchers in vault/_actions/ for each
  │                  │  ticket-state combination
  └────────┬─────────┘
           │ user clicks ↻ re-run with feedback / ▶️ go
           ▼
  ┌──────────────────┐
  │ Terminal opens   │  runs bin/run-skill-with-state.sh which:
  │                  │   1. marks state.json: amending=true / iterating=true
  │                  │   2. exports INBOX_STATE_FILE / INBOX_TICKET_KEY env
  │                  │   3. launches `claude '/pr-amend <url>'` (interactive TUI)
  └────────┬─────────┘
           │ skill runs in user's terminal — visible streaming, can interrupt
           ▼
  ┌──────────────────┐
  │ /pr-amend skill  │  at each step, calls bin/progress-tick.sh <n> 9 "<label>"
  │ (or other skill) │  → updates state.json.progress → triggers status redraw
  └────────┬─────────┘
           │ skill commits, pushes, posts PR comment, exits
           ▼
  ┌──────────────────┐
  │ trap on launcher │  clears amending=true / iterating=true
  │                  │  triggers final status redraw → row flips to ✅ done
  └──────────────────┘
```

## What this assumes

- macOS (the bin scripts use BSD-flavored tools; Linux is untested).
- [Obsidian](https://obsidian.md) installed, with a vault at `~/Documents/ObsidianVault/` (or override with `VAULT=`).
- [Claude Code](https://claude.com/claude-code) CLI installed and authenticated.
- `gh`, `jq`, `fswatch` on `PATH` (`brew install gh jq fswatch`).
- `gh auth status` showing you're logged in to GitHub.

## Install (one-shot)

```bash
brew install gh jq fswatch
gh auth login   # if not already

git clone https://github.com/CasterlyGit/workspace-tools.git ~/Documents/Dev/workspace-tools
cd ~/Documents/Dev/workspace-tools
./install.sh
```

Symlinks `skills/*.md` into `~/.claude/commands/` and `bin/*.sh` into `~/bin/`. Idempotent — re-run after pulling. Override locations with env vars:

```bash
CLAUDE_CMDS=~/.claude/commands  BIN_DIR=~/bin  \
DEV=~/Documents/Dev  VAULT=~/Documents/ObsidianVault/Specs  \
./install.sh
```

## Daily use

1. **Capture a ticket.** Drop a markdown file in any project's `inbox/`:
   ```
   ~/Documents/Dev/<repo>/inbox/<slug>.md
   ```
2. **Status page renders automatically** at `~/Documents/ObsidianVault/Specs/_status.md`. Open it in Obsidian. The new ticket shows up as `📝 ready` with a `▶️ go` button.
3. **Click `go`.** Terminal opens, `/iterate-fast` runs visibly: files the issue, branches, codes, tests, opens PR. Status row updates live with progress + ETA.
4. **Review the PR on GitHub.** If you want changes, post a comment on the PR (not in Obsidian, not in the ticket file).
5. **Click `↻ re-run with feedback`.** Terminal opens, `/pr-amend` runs: reads your comment, implements the delta, pushes, comments back. ~2-5 min.
6. **Merge.** Click `✅ merge` in the status page or hit the GitHub merge button.

## Adding a new skill

1. Drop a `<name>.md` into `skills/`. YAML frontmatter must have `description:`.
2. Re-run `./install.sh` to symlink it. The skill is immediately available as `/<name>` in Claude Code.
3. If the skill should report progress to the status dashboard, call `~/bin/progress-tick.sh <step> <total> "<label>"` at each major step. Env vars are auto-set when the launcher invokes the skill.

## What was abandoned

The `workspace_tools/` Python orchestrator (still in this repo for reference). It chained subprocesses to the `claude` CLI to run a 7-stage SDD pipeline; the architecture meant 5–10 minutes of opaque silent execution for any non-trivial ticket, and amend cycles re-ran every stage. The skills approach replaces it with one Claude Code TUI session per task — visible streaming, warm prompt cache, surgical scope.

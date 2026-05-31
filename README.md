# agent-harness

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](pyproject.toml)
[![board-sync](https://github.com/CasterlyGit/agent-harness/actions/workflows/board-sync.yml/badge.svg)](https://github.com/CasterlyGit/agent-harness/actions/workflows/board-sync.yml)

**A personal agentic dev harness that turns an Obsidian inbox ticket into a shipped pull request — one `go` click, no keyboard between.**

**Status:** v0.1 — ships PRs end-to-end on macOS; skills-based architecture live; Python orchestrator preserved as reference.

Live demo: https://casterlygit.github.io/agent-harness/

---

## Signal

- **One click to PR.** Drop a markdown file in `inbox/`, click `go` in Obsidian, watch `/iterate-fast` branch, code, run tests, and open a PR in 3–8 minutes wall clock.
- **Zero daemons.** No background process holds state. Kill everything; restart from disk. Each skill re-derives context on invocation.
- **Streaming, interruptible.** Claude Code runs in your terminal. You read along, interrupt, course-correct at any point.
- **Self-dogfooding.** This repo's own `inbox/` is wired into the harness.

---

## Architecture

```
  Obsidian vault
  inbox/<slug>.md          write a one-line ticket

        |
        |   fswatch → bin/inbox-watcher.sh → bin/inbox-process.sh
        v
  inbox-process.sh         reads inbox/.state.json,
                           renders _status.md (live dashboard),
                           emits .command launchers per ticket

        |
        |   user clicks  go  /  re-run with feedback
        v
  bin/run-skill-with-state.sh
                           1. flips state.json → iterating=true
                           2. exports INBOX_STATE_FILE / INBOX_TICKET_KEY
                           3. launches  claude '/iterate-fast <ticket>'  in a terminal

        |
        |   Claude Code runs visibly, streaming
        v
  /iterate-fast skill      branches, writes code, runs tests, pushes, opens PR.
                           Calls bin/progress-tick.sh at each step
                           → state.json updates → status page redraws

        |
        |   PR comment → user clicks  re-run with feedback
        v
  /pr-amend skill          reads latest comment, implements delta,
                           pushes, replies on the PR
```

`inbox/.state.json` is the single source of truth. The status page is a derived view. Skills are stateless workers.

---

## Skills inventory

| Skill | What it does | Target time |
|---|---|---|
| `/iterate-fast` | Inbox ticket → branch → code → tests → PR | 3–8 min |
| `/pr-amend` | Latest PR comment → implement delta → push → reply | 2–5 min |
| `/file` | Quick GitHub issue filer with board placement | < 1 min |
| `/iterate` | Brownfield orchestrator: issue → SDD pipeline → PR | varies |
| `/epic` | Decompose big ticket → N steps → one branch → one PR | varies |
| `/automate` | Greenfield: idea → new repo + project board + initial commit | varies |
| `/onboard` | Bring an existing repo into the workflow | varies |
| `/hub` | Bootstrap the master Workspace project v2 | once |
| `/board-setup` | Apply standard Status/Priority/Target fields to a Project | once |
| `/label-sync` | Apply the standard label kit to a repo (idempotent) | once |
| `/ticket` | Drop a ticket into the Obsidian Specs watcher | instant |

Each skill is a single `.md` file with a YAML `description:` frontmatter. Claude Code reads them as slash commands. Add a skill: drop a `.md` in `skills/` and re-run `./install.sh`.

---

## Setup

```bash
brew install gh jq fswatch
gh auth login

git clone https://github.com/CasterlyGit/agent-harness ~/Documents/Dev/agent-harness
cd ~/Documents/Dev/agent-harness
./install.sh
```

`install.sh` symlinks `skills/*.md` into `~/.claude/commands/` and `bin/*.sh` into `~/bin/`. Idempotent — re-run after pulling. Override paths with env vars:

```bash
CLAUDE_CMDS=~/.claude/commands  BIN_DIR=~/bin \
DEV=~/Documents/Dev  VAULT=~/Documents/ObsidianVault/Specs \
./install.sh
```

**Assumptions:**
- macOS (bin scripts use BSD tools; Linux untested)
- Obsidian vault at `~/Documents/ObsidianVault/` (override with `VAULT=`)
- Claude Code CLI installed and authenticated
- `gh auth status` shows you logged in

---

## Usage

1. Drop a markdown file in any project's `inbox/`. One sentence is enough.
2. Open `~/Documents/ObsidianVault/Specs/_status.md` in Obsidian. The ticket shows as `ready` with a `go` button.
3. Click `go`. Terminal opens. `/iterate-fast` runs visibly.
4. Review the PR on GitHub. Comment if you want changes.
5. Click `re-run with feedback`. `/pr-amend` runs.
6. Merge.

---

## Config

Magic lines (optional, first 10 lines of any inbox ticket):

```
approve: yes       # THE GATE — set yes to file the issue. Default: no.
type: bug          # Default: feature. Valid: bug | feature | polish | chore | docs | security
priority: p1       # Default: none. Valid: p0 | p1 | p2 | p3
auto-iterate: no   # Default: yes. Set "no" to file the issue but skip /iterate-fast.
```

A `# Heading` on the first line overrides the filename as the issue title.

---

## Observability

| Log | Contents |
|---|---|
| `/tmp/inbox.log` | fswatch events |
| `/tmp/inbox-iterate.log` | claude pipeline runs |
| `/tmp/inbox-watcher.log` | watcher loop |

`inbox/.state.json` in each repo is the live state map (local-only, gitignored). The GitHub issue is the canonical record once filed.

The `board-sync` CI workflow moves GitHub Project v2 cards automatically when issues and PRs change state (Backlog → In Progress → In Review → Done).

---

## Layout

```
skills/               slash command markdown prompts (Claude Code reads these)
_pipeline-prompts/    legacy 7-stage SDD prompts (research, design, implement…)
bin/                  shell scripts: inbox watcher, status renderer, launchers
workspace_tools/      legacy Python orchestrator (kept for reference)
inbox/                this repo's own inbox — dogfood
install.sh            symlinks skills → ~/.claude/commands/ and bin → ~/bin/
```

---

## Roadmap

- [x] Inbox → GitHub issue → `/iterate-fast` → PR (end-to-end)
- [x] PR feedback loop via `/pr-amend`
- [x] Live Obsidian status page with action buttons
- [x] `board-sync` CI: auto-move Project v2 cards on PR/issue events
- [x] Standard label kit + board kit applied via `/label-sync` / `/board-setup`
- [ ] Sub-stage breadcrumbs in the status page (progress bar granularity)
- [ ] `/epic` multi-step support: parallel branch fan-out
- [ ] Linux support (replace BSD `fswatch` with `inotifywait`)
- [ ] `launchd` LaunchAgent for inbox watcher (currently started from `.zshrc`)

---

## What was abandoned

The `workspace_tools/` Python orchestrator chained subprocesses to the `claude` CLI across a 7-stage SDD pipeline. Any non-trivial ticket meant 5–10 minutes of silent background execution, and amend cycles re-ran every stage. The skills approach replaces it: one Claude Code TUI session per task — visible streaming, warm prompt cache, surgical scope.

---

## Companion repos

- [curby](https://github.com/CasterlyGit/curby) — voice + gesture macOS controller; first repo fully onboarded into this harness
- [shed](https://github.com/CasterlyGit/shed) — Claude Code that learns you; handoff + skill-learning engine
- [claude-meter](https://github.com/CasterlyGit/claude-meter) — live Claude API usage meter (Übersicht widget)
- [emergency-ai](https://github.com/CasterlyGit/emergency-ai) — AI-assisted triage for emergency response
- [CasterlyGit](https://github.com/CasterlyGit/CasterlyGit) — profile hub

---

## License

MIT — see [LICENSE](LICENSE).

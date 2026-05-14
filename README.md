# workspace-tools

An agentic dev harness — ideas to shipped PRs without me touching the keyboard between.

Live demo: https://casterlygit.github.io/workspace-tools/

## The pitch

I am one person. I have more ideas than time. So I built a harness that turns a sentence in Obsidian into a shipped pull request, with Claude Code as the worker.

The flow is:

1. I write a ticket in Obsidian. A markdown file in a project's `inbox/`.
2. A status page renders automatically, listing every open ticket across every repo, with action buttons next to each row.
3. I click `go`. A terminal opens. Claude Code runs `/iterate-fast` visibly — files the GitHub issue, branches, writes code, runs tests, pushes, opens a PR.
4. I review on GitHub. If I want changes I comment on the PR, then click `re-run with feedback`. Claude reads the comment, implements the delta, pushes, comments back.
5. I merge.

There is no orchestrator process, no daemon, no web app. It is a directory of markdown files, a directory of shell scripts, and Claude Code.

## How it fits together

```
  Obsidian vault            inbox/<slug>.md            user writes a ticket,
                            _status.md                 sees a live dashboard,
                                                       clicks an action button
        |
        |   fswatch on inbox/ → bin/inbox-watcher.sh → bin/inbox-process.sh
        v
  inbox-process.sh          reads each repo's inbox/.state.json,
                            renders the status page,
                            emits .command launchers per ticket
        |
        |   user clicks  re-run with feedback  /  go
        v
  Terminal opens            bin/run-skill-with-state.sh:
                            1. flips state.json to amending=true / iterating=true
                            2. exports INBOX_STATE_FILE / INBOX_TICKET_KEY
                            3. launches `claude '/pr-amend <url>'`
        |
        |   Claude Code runs in the user's terminal, streaming visibly
        v
  /pr-amend skill           at each major step calls
                            bin/progress-tick.sh <n> <total> "<label>"
                            → updates state.json → status page redraws
        |
        v
  Skill exits               trap clears the in-progress flag,
                            row flips to "done"
```

The state.json file in each repo's `inbox/` is the single source of truth. The status page is a derived view. The skills are stateless workers.

## The pipeline, in three lines

```
Obsidian ticket  →  /file (creates GitHub issue)
GitHub issue     →  /iterate-fast (branches, codes, tests, opens PR)
PR comment       →  /pr-amend (reads comment, implements delta, pushes)
```

Each arrow is one Claude Code skill invocation. Each one is visible, interruptible, and surgical.

## Skills inventory

```
iterate-fast    file an inbox ticket as an issue, branch, code, test, push, open PR
                target 3-8 minutes wall clock

pr-amend        read latest PR comment, implement the delta, run tests,
                push, reply on the PR. Target 2-5 minutes wall clock

file            quick GitHub issue filer with sensible defaults,
                lands on the right project board automatically

iterate         brownfield orchestrator: take an issue, run the SDD
                pipeline, open a PR. Defaults to a single fast call

epic            decompose a big ticket into N sub-steps, run them on
                ONE branch, open ONE PR with all the work

automate        greenfield: turn an idea into a new repo, project
                board, and initial commit

onboard         bring an existing repo into the workflow: clone,
                project, labels, columns, issue templates

hub             bootstrap the master "Workspace" project, a Jira-like
                all-up view across every repo

board-setup     apply the standard Status / Priority / Target field
                config to a Project v2

label-sync      apply the standard label kit to a repo, idempotent

ticket          drop a ticket into the Obsidian Specs watcher
```

Each skill is a single markdown file with a YAML frontmatter `description:` and a prompt body. Claude Code reads them as slash commands. To add one, drop a `.md` file in `skills/` and re-run `./install.sh`.

## Install

```
brew install gh jq fswatch
gh auth login

git clone https://github.com/CasterlyGit/workspace-tools ~/Documents/Dev/workspace-tools
cd ~/Documents/Dev/workspace-tools
./install.sh
```

`install.sh` symlinks `skills/*.md` into `~/.claude/commands/` and `bin/*.sh` into `~/bin/`. Idempotent — re-run after pulling. Override paths with env vars:

```
CLAUDE_CMDS=~/.claude/commands  BIN_DIR=~/bin \
DEV=~/Documents/Dev  VAULT=~/Documents/ObsidianVault/Specs \
./install.sh
```

Assumptions:

- macOS. The bin scripts use BSD-flavored tools. Linux is untested.
- Obsidian, with a vault at `~/Documents/ObsidianVault/` (or `VAULT=`).
- Claude Code CLI installed and authenticated.
- `gh`, `jq`, `fswatch` on `PATH`.
- `gh auth status` shows you logged in.

## Daily use

1. Drop a markdown file in any project's `inbox/`. One sentence is enough.
2. Open `~/Documents/ObsidianVault/Specs/_status.md` in Obsidian. The new ticket shows up as `ready` with a `go` button.
3. Click `go`. Terminal opens. `/iterate-fast` runs visibly.
4. Review the PR on GitHub. If you want changes, comment on the PR.
5. Click `re-run with feedback`. `/pr-amend` runs.
6. Merge.

## Philosophy

- Solo dev, AI augmented. The harness is for one person who wants the throughput of a team. No multi-user concerns, no permissions model, no sync server.
- Files are the API. Every interaction crosses a markdown or JSON file boundary. No daemons holding state. If you kill every process the system rebuilds itself from disk on next invocation.
- Visible work beats invisible work. Skills run in the user's terminal, streaming. The user can read along, interrupt, course-correct. There is no opaque background pipeline.
- Skills are stateless workers. Each invocation re-derives context from disk. This makes amend cycles cheap and resumable.
- Fast default, opt-in depth. Single-call skills by default. Multi-stage SDD pipelines only when the ticket explicitly asks for them.
- Token budget matters. The harness is tuned to avoid wasted tool calls. Every skill exits as soon as the work is done.

## What was abandoned

The `workspace_tools/` Python orchestrator is still in this repo for reference. It chained subprocesses to the `claude` CLI to run a 7-stage SDD pipeline. The architecture meant 5 to 10 minutes of opaque silent execution for any non-trivial ticket, and amend cycles re-ran every stage. The skills approach replaces it with one Claude Code TUI session per task — visible streaming, warm prompt cache, surgical scope.

## Layout

```
skills/             slash command markdown prompts
_pipeline-prompts/  legacy SDD stage prompts (research, design, implement, ...)
bin/                shell scripts: inbox watcher, status renderer, launchers
workspace_tools/    legacy Python orchestrator (kept for reference)
inbox/              this repo's own inbox of tickets, eats its own dogfood
tests/              shell tests for the bin/ scripts
install.sh          symlink skills into ~/.claude/commands/ and bin into ~/bin/
```

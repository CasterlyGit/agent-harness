"""Workspace-tools CLI.

Two top-level commands today:

    workspace-tools iterate <issue-url|owner/repo#N|next>
    workspace-tools automate "<idea>"

Both run their pipeline deterministically: stages execute in Python, not via
a model loop. If a stage fails, the orchestrator halts and reports — there's
no silent "Stop." that ends a multi-stage run prematurely.

Adding a new top-level command is one new sub-parser + one function below.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import (
    Agent, Pipeline, PipelineHooks, Repo, StageContext,
    ensure_branch, push, pr_create, pr_open_for_branch,
    fetch_issue, parse_issue_ref, slugify,
)
from .pipelines import pick_shape, shape_for_issue
from .core.state_sink import StateSink


def cmd_iterate(args: argparse.Namespace) -> int:
    issue_ref = args.issue
    repo_full, num = parse_issue_ref(issue_ref)
    issue = fetch_issue(repo_full, num)

    # Locate or assume the local repo at ~/Documents/Dev/<name>
    dev = Path.home() / "Documents" / "Dev"
    repo_path = dev / issue.repo_name
    if not (repo_path / ".git").is_dir():
        print(f"[iterate] no local clone at {repo_path}; cloning…", flush=True)
        from subprocess import run as srun
        srun(["gh", "repo", "clone", repo_full, str(repo_path)], check=True)

    repo = Repo.at(repo_path)

    # Reuse an existing auto/<N>-* branch if any (lets resume work across
    # different slug spellings of the same issue number).
    from subprocess import run as srun
    existing_branches = srun(
        ["git", "branch", "--list", f"auto/{issue.number}-*", "--format", "%(refname:short)"],
        cwd=repo_path, capture_output=True, text=True
    ).stdout.strip().splitlines()
    if existing_branches:
        branch = existing_branches[0]
        print(f"[iterate] reusing existing branch {branch}", flush=True)
    else:
        branch = f"auto/{issue.number}-{slugify(issue.title)}"
    ensure_branch(repo, branch)

    flow_dir = repo_path / ".flow" / f"issue-{issue.number}"
    ctx = StageContext(
        repo_path=repo_path,
        flow_dir=flow_dir,
        task_id=f"issue-{issue.number}",
        issue_text=issue.aggregated_text(),
        issue_url=issue.url,
        extra={"branch": branch, "repo": repo},
    )

    # Shape selection — explicit flag wins, else infer from labels + body
    shape_name = args.shape or shape_for_issue(issue.labels, issue.body)
    stages = pick_shape(shape_name)
    print(f"[iterate] shape: {shape_name} ({len(stages)} stage(s))", flush=True)

    # State sink: writes live progress to inbox/.state.json so _status.md
    # can show stage X/N as the orchestrator advances.
    state_sink = StateSink(repo_path=repo_path, issue_number=issue.number,
                           total_stages=len(stages))

    def on_line(stage, line):
        if line.strip():
            print(f"[{stage.name}] {line[:200]}", flush=True)

    hooks = PipelineHooks(
        before_pipeline=lambda ctx: state_sink.start(shape_name, len(stages)),
        before_stage=lambda stage, ctx: state_sink.stage_start(stage.name),
        after_stage=lambda stage, ctx, res: state_sink.stage_done(stage.name, res.ok),
        after_pipeline=lambda ctx, results: state_sink.finish(all_ok=all(r.ok or r.skipped for r in results)),
        on_agent_line=on_line,
    )
    pipeline = Pipeline(stages=stages, agent=Agent(), hooks=hooks)
    run = pipeline.run(ctx, repo=repo)

    if not run.all_ok:
        print(f"\n[iterate] pipeline halted; partial branch left at {branch}", flush=True)
        return 2

    # Push the branch + open PR (or update existing)
    push(repo, branch)
    existing = pr_open_for_branch(repo, branch)
    if existing:
        print(f"[iterate] PR already open: {existing['url']}", flush=True)
        pr_url = existing["url"]
    else:
        title = issue.title
        body = (
            f"Closes #{issue.number}.\n\n"
            f"All 7 SDD stages ran via workspace-tools orchestrator. "
            f"Spec artifacts under `.flow/issue-{issue.number}/`.\n"
        )
        pr = pr_create(repo, title=title, body=body, base="main", head=branch,
                       labels=issue.labels or None)
        pr_url = pr["url"]
        print(f"\n[iterate] PR opened: {pr_url}", flush=True)

    return 0


def cmd_automate(args: argparse.Namespace) -> int:
    print("[automate] not yet implemented in the new orchestrator — coming next.", flush=True)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="workspace-tools",
                                     description="Deterministic SDD pipeline runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_it = sub.add_parser("iterate", help="run the SDD pipeline against a GitHub issue")
    p_it.add_argument("issue", help="full issue URL, owner/repo#N, or 'next' for top of project board")
    p_it.add_argument("--shape", help="pipeline shape: full | feature | bugfix | bug | quickfix | polish | chore. "
                                       "Default: inferred from issue labels + body length.",
                       default=None)

    p_au = sub.add_parser("automate", help="greenfield: turn an idea into a new project")
    p_au.add_argument("idea", help="one-line description of what to build")

    args = parser.parse_args(argv)
    if args.cmd == "iterate":
        return cmd_iterate(args)
    if args.cmd == "automate":
        return cmd_automate(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

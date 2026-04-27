"""StateSink — writes live pipeline progress into the per-repo inbox state
file so the user's `_status.md` table can show stage X/N as the agent
advances. Loose coupling: writes JSON, doesn't talk to the watcher directly.

Schema appended into <repo>/inbox/.state.json under the matching ticket entry:

    "current_stage":     "design"           # or null when idle
    "stage_index":       3                   # 1-based position in the pipeline
    "total_stages":      7
    "stage_started_at":  "2026-..."          # ISO ts of when current stage began
    "stage_history": [
      {"name":"explore",  "ok":true,  "ended_at":"2026-..."},
      {"name":"research", "ok":true,  "ended_at":"2026-..."},
      ...
    ]
    "shape":         "full"
    "last_activity": "writing src/foo.py …"  # rolling sub-stage breadcrumb
    "last_heartbeat": "2026-..."             # ticked every ~3s while a stage runs
    "last_updated":  "2026-..."

The `regenerate_status` function in inbox-process.sh renders these. This
module never touches markdown.

The heartbeat thread also appends a tiny line to the inbox iterate log
every tick — that's what wakes fswatch so `_status.md` actually
re-renders. Without it, state.json writes alone are silent (fswatch
excludes `.state.json` to avoid tight loops on its own writes)."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path


# Appending here used to be how the renderer found out about progress, via
# fswatch on the watcher. Turns out macOS FSEvents is unreliable on /tmp
# (symlinked to /private/tmp) for rapid appends to a writer-held file —
# events get coalesced or dropped, so _status.md stops redrawing.
# We still write here for human-readable diagnostics, but the renderer is
# now driven directly by the heartbeat thread (see _heartbeat_loop).
_ITER_LOG = "/tmp/inbox-iterate.log"
_RENDER_SCRIPT = "/Users/casterly/bin/inbox-process.sh"


class StateSink:
    def __init__(self, *, repo_path: Path, issue_number: int, total_stages: int):
        self.repo_path = repo_path
        self.issue_number = issue_number
        self.total_stages = total_stages
        self._state_file = repo_path / "inbox" / ".state.json"
        self._last_activity_write = 0.0
        self._heartbeat_stop: threading.Event | None = None
        self._heartbeat_thread: threading.Thread | None = None

    # ── public API matched to PipelineHooks ──────────────────────────────────

    def start(self, shape: str, total_stages: int) -> None:
        self.total_stages = total_stages
        self._mutate(lambda e: {
            **e,
            "shape": shape,
            "total_stages": total_stages,
            "current_stage": None,
            "stage_index": 0,
            "stage_started_at": None,
            "stage_history": e.get("stage_history") or [],
            "agent_done": False,
            "iterated": True,
            "last_heartbeat": _now(),
            "last_updated": _now(),
        })
        self._start_heartbeat()

    def stage_start(self, name: str, position: int) -> None:
        """`position` is the 1-based slot of this stage in the full pipeline,
        regardless of whether earlier stages were skipped. So if explore is
        skipped (artifact present) and research runs first, research is still
        position=2/7 — matches what the user expects to see."""
        self._last_activity_write = 0.0
        self._mutate(lambda e: {
            **e,
            "current_stage": name,
            "stage_index": position,
            "stage_started_at": _now(),
            "last_activity": None,
            "last_heartbeat": _now(),
            "last_updated": _now(),
        })
        self._poke_iter_log(f"[stage] {name} ({position}/{self.total_stages})")

    def note_activity(self, line: str) -> None:
        """Sub-stage breadcrumb. Called per agent stdout line; throttled to
        ~2s so we don't rewrite the JSON on every token."""
        line = (line or "").strip()
        if not line:
            return
        now = time.monotonic()
        if now - self._last_activity_write < 2.0:
            return
        self._last_activity_write = now
        snippet = line[:120]
        self._mutate(lambda e: {
            **e,
            "last_activity": snippet,
            "last_heartbeat": _now(),
            "last_updated": _now(),
        })

    def stage_done(self, name: str, ok: bool) -> None:
        self._mutate(lambda e: {
            **e,
            "stage_history": (e.get("stage_history") or []) + [
                {"name": name, "ok": ok, "ended_at": _now()}
            ],
            "last_heartbeat": _now(),
            "last_updated": _now(),
        })
        self._poke_iter_log(f"[stage-done] {name} ok={ok}")

    def finish(self, *, all_ok: bool) -> None:
        self._stop_heartbeat()
        self._mutate(lambda e: {
            **e,
            "current_stage": None,
            "stage_started_at": None,
            "last_activity": None,
            "agent_done": True,
            "ok": all_ok,
            "last_heartbeat": _now(),
            "last_updated": _now(),
        })
        self._poke_iter_log(f"[pipeline-done] ok={all_ok}")

    # ── heartbeat ─────────────────────────────────────────────────────────────

    def _start_heartbeat(self) -> None:
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="state-sink-heartbeat"
        )
        self._heartbeat_thread.start()

    def _stop_heartbeat(self) -> None:
        if self._heartbeat_stop:
            self._heartbeat_stop.set()
        self._heartbeat_thread = None

    def _heartbeat_loop(self) -> None:
        # Tick every 3s. Updates state.json's last_heartbeat AND directly
        # invokes the renderer so _status.md redraws on a guaranteed
        # cadence, regardless of fswatch reliability.
        assert self._heartbeat_stop is not None
        while not self._heartbeat_stop.wait(3.0):
            try:
                self._mutate(lambda e: {**e, "last_heartbeat": _now()})
                self._poke_iter_log("[hb]")
                self._render_now()
            except Exception:
                pass

    def _poke_iter_log(self, line: str) -> None:
        try:
            with open(_ITER_LOG, "a") as f:
                f.write(f"{line}\n")
        except OSError:
            pass

    def _render_now(self) -> None:
        """Synchronously call the renderer. Capped at 5s so a slow render
        can't pile up across heartbeats. stdout/stderr discarded — failures
        must never crash the pipeline."""
        try:
            subprocess.run(
                [_RENDER_SCRIPT],
                timeout=5, check=False,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    # ── internals ─────────────────────────────────────────────────────────────

    def _mutate(self, fn) -> None:
        """Atomic read-modify-write of the JSON file. The state.json is shared
        with inbox-process.sh, so we must not partially-write it."""
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                blob = json.loads(self._state_file.read_text() or "{}")
            except (FileNotFoundError, json.JSONDecodeError):
                blob = {}

            target_key = None
            for key, entry in blob.items():
                if not isinstance(entry, dict):
                    continue
                url = entry.get("url") or ""
                if url.rstrip("/").endswith(f"/issues/{self.issue_number}"):
                    target_key = key
                    break
            if target_key is None:
                target_key = f"issue-{self.issue_number}.virtual"
                blob.setdefault(target_key, {
                    "status": "filed",
                    "url": f"https://github.com/.../issues/{self.issue_number}",
                    "title": f"issue #{self.issue_number}",
                    "pr_num": None,
                })

            existing = blob.get(target_key) or {}
            blob[target_key] = fn(existing)

            tmp = tempfile.NamedTemporaryFile("w", delete=False,
                                              dir=str(self._state_file.parent),
                                              prefix=".state.", suffix=".tmp")
            json.dump(blob, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, self._state_file)
        except Exception as e:
            # State sink must never crash the pipeline
            print(f"[state-sink] write failed: {e}", flush=True)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

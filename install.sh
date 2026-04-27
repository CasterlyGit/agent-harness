#!/usr/bin/env bash
# install-skills.sh — set up the agentic-inbox workflow on this machine.
#
# What it does (idempotent):
#   1. Symlinks skills/*.md → ~/.claude/commands/*.md  (Claude Code slash commands)
#   2. Symlinks bin/*.sh    → ~/bin/*.sh               (helper scripts)
#   3. Creates ~/Documents/Dev (DEV root) and ~/Documents/ObsidianVault/Specs (VAULT) if missing
#   4. Backs up any existing files before replacing them
#
# Override locations with env vars:
#   CLAUDE_CMDS=~/.claude/commands  BIN_DIR=~/bin  DEV=~/Documents/Dev  VAULT=~/Documents/ObsidianVault/Specs
#
# Re-run any time after pulling — symlinks are refreshed, no data loss.

set -euo pipefail

# Preflight: required CLI tools used by bin/*.sh and the skills.
missing=()
for cmd in gh jq fswatch; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "Missing required tools: ${missing[*]}" >&2
  echo "Install with: brew install ${missing[*]}" >&2
  echo "Then make sure 'gh auth status' shows you're logged into GitHub." >&2
  exit 1
fi

REPO_DIR=$(cd "$(dirname "$0")" && pwd)
CLAUDE_CMDS=${CLAUDE_CMDS:-$HOME/.claude/commands}
BIN_DIR=${BIN_DIR:-$HOME/bin}
DEV=${DEV:-$HOME/Documents/Dev}
VAULT=${VAULT:-$HOME/Documents/ObsidianVault/Specs}

mkdir -p "$CLAUDE_CMDS" "$BIN_DIR" "$DEV" "$VAULT/_actions"

ts=$(date +%s)

link() {
  local src=$1 dst=$2
  # If dst exists and isn't already pointing at src, back it up.
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    local current=$(readlink "$dst" 2>/dev/null || true)
    if [ "$current" = "$src" ]; then
      echo "  = $dst (already linked)"
      return 0
    fi
    mv "$dst" "$dst.bak.$ts"
    echo "  ↪ backed up existing $dst → $dst.bak.$ts"
  fi
  ln -s "$src" "$dst"
  echo "  ✓ $dst → $src"
}

echo "Installing skills → $CLAUDE_CMDS"
# .md (slash commands), .json (board-kit / labels), and dirs (_pipeline, _templates)
for f in "$REPO_DIR"/skills/*.md "$REPO_DIR"/skills/*.json "$REPO_DIR"/skills/_*/; do
  [ -e "$f" ] || continue
  # strip trailing / from dir matches
  src=${f%/}
  link "$src" "$CLAUDE_CMDS/$(basename "$src")"
done

echo
echo "Installing bin scripts → $BIN_DIR"
for f in "$REPO_DIR"/bin/*.sh; do
  [ -e "$f" ] || continue
  chmod +x "$f"
  link "$f" "$BIN_DIR/$(basename "$f")"
done

echo
echo "Workspace dirs:"
echo "  DEV   = $DEV"
echo "  VAULT = $VAULT"
echo
echo "Done. Quick test:"
echo "  type \"/pr-amend <pr-url>\" inside Claude Code to verify the slash command"
echo "  loaded — Claude reads $CLAUDE_CMDS/pr-amend.md automatically."
echo
echo "To wire the Obsidian status page to a fswatch loop:"
echo "  $BIN_DIR/inbox-watcher.sh   # leave running in a Terminal tab"

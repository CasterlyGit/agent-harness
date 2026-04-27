---
description: "Drop a ticket into the Obsidian Specs watcher. Creates Specs/<project>/<title>.md so the watcher files the GitHub issue and (by default) kicks off /iterate."
---

You are running **`/ticket`**.

**Args:** `$ARGUMENTS` → free-form. First token is the project (folder under `~/Documents/ObsidianVault/Specs/`). The rest is the issue body. Examples:

- `neon-stereo youtube url option doesnt work, want it like yt music app — sign in with my account`
- `curby bug p1 voice indicator hides under menu bar`
- `feature curby system-prompt context for agents`

## What this does

Writes a markdown file to `/Users/casterly/Documents/ObsidianVault/Specs/<project>/<title>.md`. The file watcher picks it up, files the GitHub issue, adds it to the project board + Workspace hub, and (default) runs `/iterate`. See `~/Documents/ObsidianVault/Specs/README.md` for the watcher rules.

## Parse the args

1. **project** — first token. Must match an existing folder under `~/Documents/ObsidianVault/Specs/` (run `ls` to verify). If missing or unclear, ask once.
2. **type** — if the args contain `bug` / `feature` / `polish` / `chore` / `docs` / `security` as a standalone token, capture it. Default: omit (watcher defaults to `feature`).
3. **priority** — if the args contain `p0` / `p1` / `p2` / `p3`, capture it. Default: omit.
4. **auto-iterate** — if the user says "no iterate" / "don't iterate" / "file only", set `auto-iterate: no`. Default: omit (watcher defaults to yes).
5. **title** — short slug from the description (4–8 words, lowercased, hyphens). Strip filler. The filename becomes the issue title.
6. **body** — the user's description, lightly cleaned: fix obvious typos, keep their voice, don't expand or pad. One short paragraph or a few bullets is plenty.

## Write the file

Path: `/Users/casterly/Documents/ObsidianVault/Specs/<project>/<title>.md`

Format (only include magic lines that were specified — omit defaults):

```markdown
type: <type>
priority: <priority>
auto-iterate: <no>

<body>
```

If no magic lines, just write the body. Don't add a `# Heading` — the filename is the title.

Use the `Write` tool directly. Do not run `gh` — the watcher handles GitHub.

## Report

```
✅ Ticket dropped → Specs/<project>/<title>.md
   Watcher will file the issue + kick off /iterate.
```

Stay terse. Don't preview the file content back to the user — they can see it in Obsidian.

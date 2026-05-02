---
description: Summarize all uncommitted changes in the current addon's git repo — what changed, why it likely changed, and any risks.
allowed-tools: [Bash, Read, Glob, Grep]
---

Summarize all uncommitted changes in the addon at the cwd.

## Step 1 — Detect git

Run `git rev-parse --is-inside-work-tree` (silently). If not a git repo, tell the user the addon isn't under git and stop.

## Step 2 — Gather changes

Run, in parallel:
- `git status --short` — list of changed/added/deleted/untracked files
- `git diff --stat` — per-file insertion/deletion counts for tracked changes
- `git diff` — full unstaged diff
- `git diff --cached` — full staged diff
- `git log -1 --format='%h %s (%cr)'` — the last commit, for context

If there are no changes (working tree clean and nothing staged), say so and stop.

## Step 3 — Report

Print a structured summary, in this order:

**Last commit**: hash, subject, time

**Files changed** (table or bullet list):
- `path/to/file.lua` — `+12 -3` — one-line description of what changed (e.g. "added new aura filter handler", "renamed `ApplyConfig` to `RefreshConfig`")
- ...

Group related changes if there's a common theme (e.g. "Localization additions across enUS.lua + Core.lua + Settings.lua").

**Likely intent** (1–3 short bullets): your inference about what the user is working on. Be specific (e.g. "Adding support for tracking interrupts on raid frames" not "Code improvements").

**Risks / things to double-check**:
- Any new public symbols added without callers (dead code?)
- Removed symbols still referenced elsewhere (broken references — run `grep` to verify)
- New events registered but never unregistered
- TODO/FIXME/HACK comments added in this diff
- New library/dependency requirements not yet in TOC
- Version field changed but no other release-coordination changes (CHANGELOG, etc.)
- `## Interface:` not bumped if needed

**Untracked files** (if any): list them. Flag anything that looks like it shouldn't be committed (`.bak`, `.lua.swp`, IDE files, secrets).

## Hard rules

- **Read-only.** Don't run `git add`, `git stash`, `git reset`, or any mutation.
- **Don't paste the full diff** unless the user asks — the summary is the point.
- **Be specific in inference.** "Refactored UI" is useless; name the actual frames or functions.

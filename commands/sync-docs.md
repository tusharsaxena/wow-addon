---
description: Deep-analyze the current state of the addon and rewrite README.md, CLAUDE*.md, and ARCHITECTURE*.md to match — eliminating documentation drift. Includes count-claim verification, slash/COMMANDS parity, dead-export detection, and ARCHITECTURE.md scaffolding.
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write]
---

Deep-analyze the current state of the WoW addon in the cwd, then rewrite its documentation files so they accurately describe what the code does today.

## Step 0 — ARCHITECTURE.md decision

Before doing anything else, check if `ARCHITECTURE.md` exists at the addon root, and if `docs/ARCHITECTURE_*.md` files exist.

Count the addon's source files (`.lua` and `.xml` files referenced in the TOC, **excluding** `libs/` and `Libs/`).

Apply this rule:
- **< 10 source files**: a single `ARCHITECTURE.md` at the root is appropriate. If absent, propose creating one with sections: Purpose, Module map, Boot, Data flow, Settings, Slash dispatch, Saved variables, Conventions.
- **≥ 10 source files**: a top-level `ARCHITECTURE.md` index pointing to `docs/ARCHITECTURE_*.md` per topic is appropriate. If absent, propose the split layout.

If ARCHITECTURE docs already exist in some form, leave the structure alone — just sync content.

If you propose creating ARCHITECTURE docs, ask the user to confirm before scaffolding.

## Step 1 — Discover the addon

1. Locate the `.toc` file(s) in cwd. Read every one. Extract: addon name, title, version, interface versions, saved variables, library deps, full file load order.
2. List every `.lua` and `.xml` file the TOC loads. Build a mental map of: core entry point, modules, settings UI, locales, libs (skip `libs/`/`Libs/` content).
3. Read every loaded file (skip libs). Identify:
   - The addon-init pattern (Ace3 `NewAddon`, vanilla frame, etc.)
   - All slash commands registered (and their subcommands — including any `COMMANDS` dispatcher table)
   - All events registered, and which handlers they map to
   - All saved-variable scopes used (profile, char, global, etc.) and the shape of each
   - All modules and their responsibilities
   - All user-visible strings (especially un-localized ones)
   - All public APIs the addon exposes (functions on the addon table, messages it sends)
   - All schema-row paths (if there's a `Schema.lua`) — what settings exist and where they live
   - Any TODO/FIXME/HACK comments and their locations

## Step 2 — Discover the docs

Find every documentation file: `README.md`, `README.*`, `CLAUDE.md`, `CLAUDE.*.md`, `CLAUDE/*.md`, `ARCHITECTURE.md`, `ARCHITECTURE.*.md`, `docs/*.md`. List them.

For each, read the current contents and build a drift inventory across these axes:

**Stale facts** — claims in docs that contradict code:
- Numeric counts in prose or headings ("8 macros", "tracks 12 spells", "5 modules") vs. the actual count from Step 1. Flag any mismatch.
- Wrong slash commands, wrong file paths, wrong saved-variable name, wrong Interface number
- Wrong/missing dependencies, removed-but-still-listed modules
- Outdated version number anywhere docs mention it

**Slash command parity (COMMANDS ↔ README)**
- If the addon has a `COMMANDS` (or similarly named) dispatcher table:
  - Every entry in the table should appear in the README's slash-command documentation
  - Every slash command the README documents should be in the table
  - Flag both directions

**Exported API parity**
- Every function exported on the addon table that docs claim exists → verify it's still there
- Every function exported on the addon table that docs DON'T mention → flag if it looks like a public API (not a hyphenated/leading-underscore private name)

**Schema row drift**
- If the addon has a `Schema.lua`: every setting path docs cite (`db.profile.bar.texture`, etc.) should still exist in the schema. Every schema row that's user-tunable and prominent should be at least mentioned in user-facing docs.

**Orphaned references**
- Links in docs to deleted files (`docs/foo.md` that no longer exists)
- Mentions of removed functions, removed modules, removed slash subcommands

**Missing coverage**
- Code features with no doc footprint (a new module not in any module list, a new slash subcommand not documented)

**Dead exports** (separate finding, often surfaces while building the API parity check)
- Functions on the addon table with **zero callers** in the addon's own `.lua` files (excluding libs). Use `grep -r` to verify. List these as candidates for deletion — don't auto-delete.

## Step 3 — Show drift before writing

Print the drift inventory to the user as a structured summary, grouped by doc file. One line per item. Example:

```
DRIFT INVENTORY

README.md
  STALE: "8 macros" — actual count is 10 (LIST in core/Macros.lua:42)
  STALE: /kcm dispatcher prefix — actual is /cm (core/Slash.lua:18)
  ORPHAN: links to docs/old-spec.md (file deleted in 73a2f1c)
  MISSING: /cm preview subcommand documented nowhere

CLAUDE.md
  STALE: claims schema lives in Settings.lua — moved to Schema.lua

ARCHITECTURE.md
  MISSING: Castbar module added in 1.6.0, not in the module map

DEAD EXPORTS (candidates for deletion, not auto-removed)
  core/Util.lua:88   addon.ParseColor    (zero callers)
  core/Util.lua:103  addon.PrintLSMList  (zero callers)
```

If the drift list is large (>10 items) or any item is ambiguous, ask for confirmation before applying. For small/obvious drift, proceed.

## Step 4 — Rewrite

For each doc file:
- **README.md**: keep its overall shape. Update each section to reflect current state. Don't invent sections that weren't there. Preserve the user's voice — match the existing tone, formatting, and emoji usage (or absence).
- **CLAUDE.md** (and `CLAUDE.*.md`): project context for future Claude sessions. Update against your Step 1 map. Keep it concise (CLAUDE.md is loaded into every session's context).
- **ARCHITECTURE.md** (and variants): structural/design documentation. Update component descriptions, dataflow, dependency relationships, lifecycle.

Use `Edit` for surgical updates. Only `Write` (full rewrite) if the file is completely out of date or the diff would be larger than the rewrite.

**Preserve line endings.** Detect each file's existing line endings (LF or CRLF) and write the same. The plugin's CRLF hook handles `.gitattributes`-declared CRLF repos automatically, but writing the right ending the first time keeps diffs clean.

## Step 5 — Report

Print a summary:
- Files updated (with line-count delta per file)
- Files unchanged (already accurate)
- **Dead exports flagged** (separate section — these are NOT auto-removed; the user decides)
- Anything you couldn't reconcile (e.g. ambiguous intent, missing context) — flag for the user
- A reminder to review the diffs before committing

## Hard rules

- **Don't invent features.** If the README claims a feature you can't find in code, ASK before deleting — it might be intentional/aspirational.
- **Don't add documentation for things the user didn't document.** If there's no "Configuration" section currently, don't add one.
- **Don't bump the version.** Even if you find drift in version numbers, do NOT change `## Version:` in the TOC, the `VERSION` constant in code, or the README badge URL. Changing the version is `/wow-addon:version-bump`'s job.
- **Don't auto-delete dead exports.** Surface them; the user decides.
- **Don't touch LICENSE, CHANGELOG.md, TODO.md, or any file that isn't a project doc.**
- **Don't commit.**

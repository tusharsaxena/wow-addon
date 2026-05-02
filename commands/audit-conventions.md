---
description: Walk every WoW addon under cwd (or a given root) and report drift in shared conventions — Interface version, library versions, structural patterns. Read-only.
argument-hint: [root-path]   # defaults to cwd
allowed-tools: [Read, Glob, Grep, Bash]
---

Audit cross-addon convention consistency for every WoW addon under: **$ARGUMENTS** (defaults to cwd if empty).

This is a read-only report. Useful when you've adopted a new pattern in one addon and want to know which siblings diverge.

## Step 1 — Discover addons

1. Resolve the root: `$ARGUMENTS` if non-empty, otherwise cwd.
2. Find every directory at depth ≤ 2 from the root that contains a `*.toc` file matching its directory name (the standard WoW addon convention: `Foo/Foo.toc`). Each such directory is an addon.
3. If zero addons found, tell the user and stop.
4. List the addons found before proceeding.

## Step 2 — Per-addon scan

For each addon, collect (silently — no per-addon output during scan):

**TOC**
- `## Interface:` value (full comma-separated string)
- `## Version:`
- `## Author:`
- `## SavedVariables:` and `## SavedVariablesPerCharacter:`
- `## OptionalDeps:` (parsed list)
- `## X-License:`
- Whether `#@no-lib-strip@` / `#@end-no-lib-strip@` pragmas wrap library entries

**Library set** (look at file names referenced in TOC and folders under `libs/` or `Libs/`)
- LibStub version (if visible)
- AceAddon-3.0 version (read the file's header comment for `-- $Id$` or version constant)
- AceDB-3.0 version
- AceConfig-3.0 version
- AceGUI-3.0 version
- LibSharedMedia-3.0 version
- Any other libs present

**Structural patterns** (grep across `*.lua` excluding `libs/` and `Libs/`)
- Boot pattern: does the addon use `LibStub("AceAddon-3.0"):NewAddon(...)`? Note mixins.
- Slash dispatch: is there a single `COMMANDS` (or similarly named) table that the slash handler iterates? Or are subcommands handled via if/elseif?
- Settings layer: is there a `Schema.lua` (or similarly named) file? Does it have a row-builder pattern, or is it ad-hoc?
- Settings UI registration: is `Settings.RegisterAddOnCategory` (12.0 API) used, or the old `InterfaceOptions_AddCategory`?
- Print helper: is there a `CHAT_PREFIX` constant? Is `print` shadowed/wrapped to route through it? Or are raw `print(...)` calls scattered?
- Saved-vars wiring: AceDB profile/char/global, or vanilla `MyAddonDB = MyAddonDB or {}` merge?

**Docs**
- Has `README.md`? `CLAUDE.md`? `ARCHITECTURE.md` (single)? `docs/ARCHITECTURE_*.md` (split)?
- README has badge row? Version History table?

**Git** (if applicable)
- Has `.gitattributes` declaring CRLF for `.lua` / `.xml` / `.md`?
- Has `.pkgmeta`?

## Step 3 — Cross-addon drift report

Group findings into sections. Within each, list the *minority* (the addons that diverge from the majority pattern):

**TOC consistency**
- `## Interface:` — list the unique values seen across addons. If more than one value: list each value with the addons that use it. If all match: print "✓ all addons on `<value>`".
- `## Author:` — same treatment
- `## X-License:` — same treatment
- TOC pragma usage (`#@no-lib-strip@`) — list addons missing it

**Library version drift**
- For each library: list unique versions seen and which addons use which. Highlight any addon on a notably older version.

**Structural pattern adoption** (for each pattern, list addons that DON'T follow the majority)
- Ace3 `NewAddon` boot
- Single `COMMANDS` slash dispatcher table
- Schema-driven settings layer
- Modern `Settings.RegisterAddOnCategory` (12.0)
- Single `CHAT_PREFIX` + routed `print`

**Documentation gaps**
- Addons missing README, CLAUDE.md, ARCHITECTURE.md
- Addons whose README lacks the badge row / Version History table (if the *majority* of siblings have these)

**Git hygiene**
- Addons missing `.gitattributes` (in projects where siblings have it)
- Addons missing `.pkgmeta` (in projects where siblings have it)

## Step 4 — Suggest follow-up actions

After the report, suggest concrete next commands the user could run to close drift, e.g.:

```
SUGGESTED FOLLOW-UPS

  Bring all addons to Interface 120000,120001,120005:
    cd <root> && /wow-addon:bump-interface 120000,120001,120005

  Normalize PrettyChat's README to match KickCD's structure:
    cd <root>/prettychat && /wow-addon:normalize-readme <root>/KickCD

  Sync docs in BuffTextNotifications (its README and code likely drifted):
    cd <root>/BuffTextNotifications && /wow-addon:sync-docs
```

Only suggest follow-ups for drift that the report actually surfaced. Don't suggest fixes for non-issues.

## Hard rules

- **Read-only.** No edits, no commits, no `git add`.
- **Don't pick a "winner".** Report drift; let the user decide which side is the convention. (Exception: when one pattern is *clearly* deprecated by Blizzard — e.g. `InterfaceOptions_AddCategory` was removed in 10.0 — note that explicitly.)
- **Skip `libs/`, `Libs/`, `.git/`** during all scans.
- **Be terse.** A drift report bloated with non-issues is unread. Skip categories with no drift; print "✓ consistent" lines only as headers, not per-addon.

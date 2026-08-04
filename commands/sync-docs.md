---
description: Deep-analyze the current state of the addon and rewrite README.md, CLAUDE*.md, DEPENDENCIES.md, and ARCHITECTURE*.md to match — eliminating documentation drift. Includes count-claim verification, slash/COMMANDS parity, dead-export detection, toolchain-vs-DEPENDENCIES.md drift, and ARCHITECTURE.md / CLAUDE.md / DEPENDENCIES.md scaffolding.
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write]
---

Deep-analyze the current state of the WoW addon in the cwd, then rewrite its documentation files so they accurately describe what the code does today.

## Step 0 — Doc layout decisions

Before doing anything else, check the addon's doc layout against the Ka0s WoW Addon Standard's fixed structure (documentation). The **root** ships exactly three docs plus `LICENSE`, and never a fourth: a **full** `README.md`, a **stub** `CLAUDE.md`, and `DEPENDENCIES.md` (documentation-§7). Everything else lives under `docs/`, which carries the canonical trio — `docs/ARCHITECTURE.md`, `docs/testing.md` and `docs/smoke-tests.md` — plus the four **required** topic-detail docs: the generated `docs/test-cases.md`, `docs/performance.md`, `docs/perf-runs/README.md` and the generated `docs/complexity.md`, and any further topic-detail docs. There is **no** `docs/agent-context.md` (documentation-§3). This layout is fixed; it does **not** vary with addon size.

### ARCHITECTURE.md decision

`ARCHITECTURE.md` belongs under `docs/` as part of the canonical trio. Check whether `docs/ARCHITECTURE.md` exists (or an `ARCHITECTURE.md` in some other location/variant).
- If it already exists in some form, **leave the structure alone — just sync content.**
- If absent, propose creating `docs/ARCHITECTURE.md` with the standard's sections: Overview, Module Map, Settings Schema, Message Bus (named messages with sender/payload/consumers), Slash Commands, Event Subscriptions, Taint Notes, Known Limitations.

### CLAUDE.md decision

The root `CLAUDE.md` is a **stub** — identity, `## Standards compliance (read first)`, a pointer list into `docs/`, and the green gate (documentation-§2). It is the **only** agent brief a Ka0s addon ships.
- If it is already in that shape, **leave the structure alone — just sync content.**
- If it is missing, propose creating the stub.
- If it carries a **full** brief inline, flag it: the durable per-addon detail belongs in `docs/ARCHITECTURE.md`, and the rest is scaffolding that does not belong in the repo at all.

### `DEPENDENCIES.md` decision

Root `DEPENDENCIES.md` is **mandatory** (documentation-§7): every piece of software needed to build, run, test or release the addon, split **runtime (in-game) / development / release-and-assets**, with copy-pasteable WSL2 / Ubuntu install commands and a one-line verification per tool. It answers *what to install*; `docs/testing.md` answers *how to verify* — the two point at each other and neither restates the other.

This command is the one that can write it, because it is the one that reads the repo. Every entry **MUST** be **evidence-based** — a `file:line`, a script's `import`, a documented command — and a speculative entry is worse than an omission, because a reader who installs three unnecessary things stops trusting the list and then misses the one that mattered. Build the list from what Step 1 actually found: the TOC's `## Dependencies` / `## OptionalDeps`, the interpreter and version the harness requires (the headless kit uses `setfenv`, which is Lua 5.1-only — state that as a requirement with its reason, never a preference), `luacheck` and its `.luacheckrc`, `lizard` for `docs/complexity.md`, anything the tests shell out to, and anything a script or asset-regeneration step imports. Note the Ubuntu 24.04 trap: `pip install <tool>` fails on PEP 668's `EXTERNALLY-MANAGED` marker, so the instruction that works is `pipx`.

- If it exists, **sync it against the evidence** — a dependency added since it was written, or a tool no longer used, is drift like any other. Report each change with what proved it.
- If it is absent, propose creating it (an undocumented toolchain is anti-pattern #50) and confirm before writing, as with the other scaffolded docs.
- If the repo genuinely has no release/asset tooling, the release section says so plainly. "None" is a **result**; a missing section reads as an omission.

### CRITICAL — `docs/agent-context.md` MUST NOT exist

**If the addon has a `docs/agent-context.md`, that is a compliance failure, not a doc to sync** (documentation-§3, anti-pattern #49). It is `NEW_ADDON_CONTEXT.md` — the **scaffolding pack** — which is fetched at runtime and never stored. Every question it answers is answered the moment the addon exists, and because it is loaded as *working context* a stale copy gets **followed**: a pack still showing how to hand-write a debug console, a dispatcher or a harness will get one hand-written in an addon that replaced all three with `LibKa0s` (#47). No gate can see it — no test covers a doc, lint does not read prose.

Do **not** sync its content. Instead:
1. Read it and identify anything genuinely **addon-specific** that accumulated in it — real invariants, real module structure, real hard rules for *this* addon.
2. Move that content to its proper home: structure and invariants → `docs/ARCHITECTURE.md`; hard rules → the root `CLAUDE.md` stub.
3. **Delete the file.** The pack's own generic content — kickstart walkthrough, starter tree, starter snippets, definition-of-done — is deleted outright, never migrated.
4. Fix every reference to it: the `CLAUDE.md` pointer list, `docs/*.md`, and any Claude memory file that names it.

Report the deletion and what was migrated. This one does **not** wait for confirmation — the standard forbids the file.

### Confirmation

If you propose creating or restructuring either doc (ARCHITECTURE or CLAUDE), ask the user to confirm before scaffolding.

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

Find every documentation file: `README.md`, `README.*`, `CLAUDE.md`, `CLAUDE.*.md`, `CLAUDE/*.md`, `DEPENDENCIES.md`, `ARCHITECTURE.md`, `ARCHITECTURE.*.md`, `docs/*.md`, `docs/**/*.md` (the nested one that exists today is `docs/perf-runs/README.md`). List them.

**Two of them are generated and are not synced by hand:** `docs/test-cases.md` (the inventory the harness emits) and `docs/complexity.md` (the `lizard` report, `performance-§10`). Read both — a count claim elsewhere in the docs must agree with `test-cases.md`, and `complexity.md` dates itself in its own header — but never edit their numbers. `test-cases.md` is refreshed by regenerating it; `complexity.md` is regenerated at **release** by `/wow-addon:bump-version`. A hand-edited complexity report is worse than an absent one because it reads as measured (anti-pattern #51). If `complexity.md`'s header is older than the last release, that is a **finding** to report, not something to fix here.

For each, read the current contents and build a drift inventory across these axes:

**Stale facts** — claims in docs that contradict code:
- Numeric counts in prose or headings ("8 macros", "tracks 12 spells", "5 modules") vs. the actual count from Step 1. Flag any mismatch.
- Wrong slash commands, wrong file paths, wrong saved-variable name, wrong Interface number
- Wrong/missing dependencies, removed-but-still-listed modules
- **`DEPENDENCIES.md` vs. what the repo actually needs** — a tool the tests or a script now require but the file does not name; a tool named there that nothing in the repo uses any more; an install command that no longer works (`pip install <tool>` on Ubuntu 24.04); a stated Lua version that disagrees with what the harness requires. Cite the evidence for each direction.
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
- **CLAUDE.md** (root **stub**): project context for future Claude sessions, and the only agent brief in the repo. Update against your Step 1 map. Keep it short — it loads into every session's context — and keep the detail in `docs/ARCHITECTURE.md`. There is no `docs/agent-context.md`; see the CRITICAL note in Step 0.
- **`docs/ARCHITECTURE.md`** (and variants): structural/design documentation. Update component descriptions, dataflow, dependency relationships, lifecycle.
- **`DEPENDENCIES.md`** (root): the toolchain contract. Update entries against the evidence from Step 1, keeping the runtime / development / release-and-assets split and each entry's install command plus its verification line. Never add an entry you cannot point at a file for.

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
- **Don't bump the version.** Even if you find drift in version numbers, do NOT change `## Version:` in the TOC, the `VERSION` constant in code, or the README badge URL. Changing the version is `/wow-addon:bump-version`'s job.
- **Don't auto-delete dead exports.** Surface them; the user decides.
- **Don't hand-edit a generated doc.** `docs/complexity.md` and `docs/test-cases.md` are produced by tools, not written. Report staleness; never edit the numbers, and never run `lizard` here — the complexity report's checkpoint is **release**, and it MUST NOT gate a commit (`performance-§10`).
- **Don't invent a dependency.** Every `DEPENDENCIES.md` entry traces to something in this repo. If you suspect a requirement but cannot evidence it, say so in words or leave it out.
- **Don't touch LICENSE, CHANGELOG.md, TODO.md, or any file that isn't a project doc.**
- **Don't commit.**

---
description: Deep-analyze the current state of the addon and rewrite README.md, CLAUDE*.md, DEPENDENCIES.md, and ARCHITECTURE*.md to match — eliminating documentation drift. Includes count-claim verification, slash/COMMANDS parity, dead-export detection, toolchain-vs-DEPENDENCIES.md drift, a comment-citation check over the addon's own source (a comment naming a path that does not exist, a caller that does not call, or a version the tree does not stamp, reported with file:line and corrected only on confirmation, comment-only), and ARCHITECTURE.md / CLAUDE.md / DEPENDENCIES.md scaffolding.
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write]
---

Deep-analyze the current state of the WoW addon in the cwd, then rewrite its documentation files so they accurately describe what the code does today.

## Step 0 — Doc layout decisions

Before doing anything else, check the addon's doc layout against the Ka0s WoW Addon Standard's fixed structure (documentation). The **root** ships exactly three docs plus `LICENSE`, and never a fourth: a **full** `README.md`, a **stub** `CLAUDE.md`, and `DEPENDENCIES.md` (documentation-§7). Everything else lives under `docs/`, which carries the canonical trio — `docs/ARCHITECTURE.md`, `docs/testing.md` and `docs/smoke-tests.md` — the five **verification-and-record** docs: the generated `docs/test-cases.md`, `docs/performance.md`, `docs/perf-analysis/README.md`, `docs/automated-tests/README.md` and the generated `docs/automated-tests/RESULTS.md` — and the **six unconditional Tier 1 topic-detail docs**: `docs/scope.md`, `docs/module-map.md`, `docs/schema.md`, `docs/settings-panel.md`, `docs/data-flow.md`, `docs/common-tasks.md`, plus whatever **Tier 2** triggers have fired and any **Tier 3** addon-specific docs (documentation-§3). A standalone `docs/complexity.md` is **retired** (v2.19.0), as are `docs/file-index.md` and `docs/conventions.md` (v2.23.0) — finding one is a pre-adoption finding to report, never a doc to keep in sync. There is **no** `docs/agent-context.md` (documentation-§3). This layout is fixed; it does **not** vary with addon size.

**Sync `## Documentation map` against the directory, in both directions.** `docs/ARCHITECTURE.md`'s tenth mandated section registers every `.md` under `docs/` in exactly one of its four tables — Required, Conditional, **Verification and record** and Addon-specific (documentation-§3). It drifts the way every register does — a doc is added and the row is not, a doc is renamed and the row keeps the old name — and it is the one part of the doc set whose check is purely mechanical, so do it properly: every file on disk has a row, every row resolves to a file, each Tier 2 row whose doc is absent carries a *Not applicable* status **and** its trigger, the **Verification and record** table carries its six standing rows (`testing.md`, `smoke-tests.md`, `test-cases.md`, `performance.md`, `automated-tests/README.md`, `automated-tests/RESULTS.md`) and nothing else — `perf-analysis/README.md` belongs in Conditional with its trigger, in both of its states, and the hub's own row is optional and never synced in or out, and the frozen directories (`audits/`, `reviews/`, `automated-tests/`, `perf-analysis/`, `pending/`, `superpowers/`, `investigations/`) are named once each rather than enumerated per run — `perf-analysis/` and `automated-tests/` get **one** row apiece for the store, never a row per dated bundle. A **missing Tier 1 doc is reported, not stubbed** — that is a compliance finding for `/wow-addon:standards-audit`, and a placeholder written here would close the finding without answering the question the doc exists to answer.

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

This command is the one that can write it, because it is the one that reads the repo. Every entry **MUST** be **evidence-based** — a `file:line`, a script's `import`, a documented command — and a speculative entry is worse than an omission, because a reader who installs three unnecessary things stops trusting the list and then misses the one that mattered. Build the list from what Step 1 actually found: the TOC's `## Dependencies` / `## OptionalDeps`, the interpreter and version the harness requires (the headless kit uses `setfenv`, which is Lua 5.1-only — state that as a requirement with its reason, never a preference), `luacheck` and its `.luacheckrc`, `lizard` for the bundle's complexity suite, anything the tests shell out to, and anything a script or asset-regeneration step imports. Name each tool's **own** package manager, not the one you reached for last: `luacheck` is a Lua rock (`sudo luarocks install luacheck`), `lizard` is a Python package (`pipx install lizard`). For the Python ones, note the Ubuntu 24.04 trap: `pip install <tool>` fails on PEP 668's `EXTERNALLY-MANAGED` marker, so the instruction that works is `pipx`.

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

Find every documentation file: `README.md`, `README.*`, `CLAUDE.md`, `CLAUDE.*.md`, `CLAUDE/*.md`, `DEPENDENCIES.md`, `ARCHITECTURE.md`, `ARCHITECTURE.*.md`, `docs/*.md`, `docs/**/*.md` (the nested **live** ones are `docs/perf-analysis/README.md` and `docs/automated-tests/README.md` / `RESULTS.md`; the `.md` files inside a dated `docs/perf-analysis/<run>/` or `docs/automated-tests/<run>/` bundle are frozen evidence — list the store, not its bundles' contents). List them.

**Two of them are generated and are not synced by hand:** `docs/test-cases.md` (the inventory the harness emits) and the automated-test record — `docs/automated-tests/RESULTS.md` plus the frozen per-run bundles (`automated-tests-§1/§4`). Read both — a count claim elsewhere in the docs must agree with `test-cases.md`, and the newest `RESULTS.md` row dates the record — but never edit their numbers. `test-cases.md` is refreshed by regenerating it; the record is regenerated at **release** by `/wow-addon:bump-version`. A hand-edited complexity record is worse than an absent one because it reads as measured (anti-pattern #51). If the newest row is older than the last release, that is a **finding** to report, not something to fix here.

For each, read the current contents and build a drift inventory across these axes:

**Stale facts** — claims in docs that contradict code:
- Numeric counts in prose or headings ("8 macros", "tracks 12 spells", "5 modules") vs. the actual count from Step 1. Flag any mismatch.
- Wrong slash commands, wrong file paths, wrong saved-variable name, wrong Interface number
- Wrong/missing dependencies, removed-but-still-listed modules
- **`DEPENDENCIES.md` vs. what the repo actually needs** — a tool the tests or a script now require but the file does not name; a tool named there that nothing in the repo uses any more; an install command that never worked or no longer does (`pip install <tool>` on Ubuntu 24.04; a Lua rock like `luacheck` handed to `pipx`); a stated Lua version that disagrees with what the harness requires. Cite the evidence for each direction.
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

### Comment-citation check

A comment that names a file, a line or a caller is documentation, and it drifts exactly like a README does — except that nothing reads it but the next person to touch that function, and no gate can see it. `luacheck` does not read prose, no test covers a comment, and a header block naming `core/DebugLog.lua` in a repo whose `core/` never held that file survives every green suite indefinitely. The same class shows up as a comment naming a reader that does not read, a member that no longer exists, or a `file:line` that resolves to something unrelated. Treat it as a drift axis of its own.

**Scope.** The addon's *own* source and config: `.lua`, `.xml`, `.toc`, `.luacheckrc`, `.pkgmeta`. **Exclude `libs/`, `Libs/` and `tests/_kit/`** — those are vendored payloads, byte-identical to their upstream tag, and a comment inside them is upstream's to fix; editing one reddens the repo's vendor-sync gate. Read only **comment** text: Lua `--` lines and `--[[ … ]]` blocks, XML `<!-- … -->`, and `#` lines in `.toc`/`.pkgmeta`. A path or a name inside a string literal, a key or a value is not a citation and is not in scope.

**Extract three kinds of token, and resolve each:**

- **Path-like tokens** — anything shaped `some/dir/File.lua`, `File.xml`, `docs/testing.md`, with an optional `:N` or `:N-M` suffix. Resolve the path relative to the repo root first, then relative to the commenting file's own directory. Report it when **no such file exists**. When the path resolves and carries a line suffix, check the suffix too: report a `:N` (or a range whose end) that is **past the end of the file**. A line number that resolves but now points at unrelated code is *not* mechanically detectable — see the limits below.
- **`Symbol.Member` references** — dotted or colon-qualified names such as `KCM.DebugLog.AddLine`, `Core.ApplySkin`, `O.AceGUI`, `Kit.assertSurfaceParity`. Report one that has **no call site**: `grep -rn` the member name across the addon's own `.lua`/`.xml` (same exclusions) and find zero definition and zero call. Resolve against `libs/` and `tests/_kit/` as well when the root is a vendored table — a comment may legitimately name a library member the addon only calls indirectly, and a hit anywhere in the loaded tree clears it.
- **Version citations** — a comment naming a version the tree itself stamps somewhere. Two shapes qualify, and they qualify because each has an authority in the repo to be checked against; that is the whole of what separates them from prose that merely holds a number. **A migration step**, shaped `v6->v9` or `v1→v2` or "bumps the stamp to 2": resolve it against the migration table's own highest `to =` (`grep -n 'to = ' core/Database.lua`, or wherever the runner lives) and report a step naming a version the table does not define. **A bundled-library tag**, shaped `v1.8.3` quoted inside a sentence about what this build vendors: resolve it against the `Bundles [LibKa0s](…) vX.Y.Z (MIT).` provenance line in the root `CLAUDE.md` — the same line `tests/test_vendor_sync.lua` reads, with no fallback — and report a quoted tag the line does not carry. A version with no such authority in the tree is prose, and stays unreported.

**Keep the false-positive rate near zero, because a noisy check gets ignored and then the real hit rides through with it.** Do not report:

- A root that is a Blizzard global or a live client API — the addon does not define it and is not expected to.
- Prose that merely contains a dot: sentence-ending words, `e.g.`, ellipses, a decimal number, a URL's host, and a version string with **no authority in the tree** — the version-citation rule above names the only two shapes that have one, and everything else numeric stays prose. Require a path token to end in a known source/doc extension, and a symbol token to be at least two `[A-Za-z_][A-Za-z0-9_]*` segments with the final segment starting upper-case or matching a name Step 1 actually found on the addon table.
- A member reached only through a vendored library's own dispatch, when a grep of the loaded tree finds it.

**What this check cannot see, stated plainly so nobody assumes it is covered:** a comment that is *countably* wrong — "all four of `PollSpell`'s exits" over a function with two — parses as prose, names nothing that fails to resolve, and is out of this check's reach. So is a self-referential explanation ("`O.AceGUI` is reached through `O.AceGUI`"), a stale rationale whose code still exists, and a duplicated paragraph. Those stay a reviewer's job. This check closes the mechanical half: **a named path that is not there, a named caller that does not call, and a named version the tree does not stamp.**

**The edit boundary — identical in shape to `/wow-addon:revendor-standards`'s, and deliberately so.** Widening what this command *reads* does not widen what it may *write*. Every comment-citation hit is **reported with `file:line`** in the Step 3 inventory and applied **only on the user's explicit confirmation**; silence is a decline, not a default. When they confirm, the edit is **comment-only** — the text of a comment or a commented header line, and nothing else. If correcting the citation would require touching a line that runs, do not edit it: report it and say why. And **never guess a target** — a comment naming a file that does not exist may mean the file was renamed, was deleted, or was never right; the user names the replacement, or the item stays flagged. Deleting a comment outright is a correction like any other, and needs the same confirmation. The two commands differ only in what they cite: `revendor-standards` corrects references to the **standard**, this one corrects references to **this repo**.

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

COMMENT CITATIONS — comment-only, needs your confirmation before anything is written
  modules/Bar.lua:5      NO SUCH PATH: "core/DebugLog.lua" — core/ holds DebugLogSetup.lua
  modules/Bar.lua:86     NO SUCH PATH: "core/DebugLog.lua" — same block, repeated
  core/CoreSetup.lua:21  NO SUCH PATH: "modules/DebugLog.lua" — modules/ holds Artwork, Canvas,
                         Registry, SunnArt, SunnArtPacks, Unlock
  settings/Slash.lua:111 NO CALL SITE: comment names settings/Panel.lua as a reader of
                         FormatSchemaValue; Panel.lua does not reference it
  core/Util.lua:40       LINE PAST EOF: "docs/testing.md:210" — the file has 96 lines
  core/Database.lua:195  NO SUCH VERSION: comment describes the "v6->v9" migration;
                         the MIGRATIONS table at :19 stops at to = 8
  tests/test_vendor_sync.lua:14  NO SUCH VERSION: header quotes v1.8.3; CLAUDE.md's
                         provenance line carries v1.25.0
```

If the drift list is large (>10 items) or any item is ambiguous, ask for confirmation before applying. For small/obvious drift, proceed. **The `COMMENT CITATIONS` block is exempt from "small/obvious proceeds"** — every item in it is confirmed before anything is written, however mechanical it looks, and each correction's replacement text is named by the user, not guessed.

## Step 4 — Rewrite

For each doc file:
- **README.md**: keep its overall shape. Update each section to reflect current state. Don't invent sections that weren't there. Preserve the user's voice — match the existing tone, formatting, and emoji usage (or absence). Three exceptions, where the shape itself is wrong and `documentation-§1` says so:
  - **The README MUST NOT carry a bundled-library inventory** (anti-pattern #58). That is `## Libraries`, `## Bundled libraries`, `## Libraries and credits`, `## Credits and libraries`, `## Credits and bundled libraries` — **and** a library roll-call smuggled into the intro paragraph with no heading at all, which is where the rule is most often satisfied in letter and broken in fact. The Ace3 / LibSharedMedia / LibDataBroker / LibDBIcon list, the "everything ships inside the addon, nothing else to install" library prose and the `Bundles [LibKa0s] …` sentence all come out together. Which libraries a build vendors is a **contributor** fact and it already has two homes read by the people it is for — root `DEPENDENCIES.md` (`documentation-§7`) and `docs/ARCHITECTURE.md` (`documentation-§3`) — and a third copy on the player-facing page is the one place no gate has ever looked.
    **What survives is external credit and nothing else.** If the section also carried a third-party artist, a font or a sound pack, keep **only** those lines, as a plain `## Credits` (`documentation-§1` item 13) placed **last**, after `## Version History`. If nothing external remains, delete the section outright — and with it any link, TOC row or cross-reference elsewhere in the README that pointed at the deleted heading, since a live link to a heading you removed is the same failure one step removed. Removing content is the one case where you may drop a section the user wrote; say plainly in the report what came out and what (if anything) was kept.
  - **The standard badge is not a link** (`documentation-§1`). If you find `[![Standard](https://img.shields.io/badge/Ka0s-WoW_Addon_Standard-yellow)](https://github.com/tusharsaxena/WowAddonStandards)`, strip the wrapper and leave the bare `![Standard](…)`. Never add the wrapper back.
  - **The `LibKa0s` provenance line belongs in the root `CLAUDE.md`**, not here — see below.
- **CLAUDE.md** (root **stub**): project context for future Claude sessions, and the only agent brief in the repo. Update against your Step 1 map. Keep it short — it loads into every session's context — and keep the detail in `docs/ARCHITECTURE.md`. There is no `docs/agent-context.md`; see the CRITICAL note in Step 0.
  - **If the addon vendors `LibKa0s`, this file carries the provenance line** — `Bundles [LibKa0s](https://github.com/tusharsaxena/LibKa0s) vX.Y.Z (MIT).` (`documentation-§2`). It moved here from `README.md` at LibKa0s v1.8.1 / test-kit revision 9, and the consumer-side vendored-payload gate (`tests/test_vendor_sync.lua`, `testing-§11`) reads it from `CLAUDE.md` with **no fallback**, so a line left in the README reads to the gate as no line at all. If you find it only in the README, **move** it — same commit, same version string, no second copy — and do not restate the tag from memory or from the sibling `LibKa0s` checkout's HEAD: carry across whatever version the README's line named, and if it names none, report the gap rather than inventing a tag. A **missing** line is a gate failure, not a skip, so say so loudly.
- **`docs/ARCHITECTURE.md`** (and variants): structural/design documentation. Update component descriptions, dataflow, dependency relationships, lifecycle.
- **`DEPENDENCIES.md`** (root): the toolchain contract. Update entries against the evidence from Step 1, keeping the runtime / development / release-and-assets split and each entry's install command plus its verification line. Never add an entry you cannot point at a file for.

Then, and only after the user has confirmed the `COMMENT CITATIONS` block item by item, apply the confirmed **comment-only** corrections in the source files those items name. Nothing in that block applies without an answer, nothing outside a comment is touched, and an item whose replacement text the user did not name stays flagged and unedited.

Use `Edit` for surgical updates. Only `Write` (full rewrite) if the file is completely out of date or the diff would be larger than the rewrite.

**Write the DECLARED line ending, not the observed one.** Ask git what the repo declares for the file — `git check-attr eol -- <path>` — and write that: CRLF in a client-bound repo, LF in one that ships nothing to the WoW client (`line-endings-§2`). Do **not** simply mirror what the file happens to carry: a file whose endings disagree with the declaration is a **straggler**, and preserving it faithfully propagates the defect. The plugin's line-ending hook normalizes to whatever the repo declares, in either direction, but writing the right ending the first time keeps diffs clean. Where nothing is declared, preserve what is there.

### The de-AI pass on the README (MUST)

`documentation-§1` MUSTs a **de-AI writing pass** on every `README.md` edit (anti-pattern #77): run the `/humanize` skill, or audit against a published AI-writing pattern catalogue, and fix what it finds **before** the change is committed.

It binds the README and nothing else. `docs/`, `CLAUDE.md`, `DEPENDENCIES.md` and code comments are contributor surfaces and are deliberately exempt — do not run it over them, and do not "improve the voice" of a comment. Apply it to **what this command changed**, not to the whole file: a README already through the pass is not re-audited section by section on every later edit.

What the pass looks for, so it is not a vibe check: uniform paragraph and sentence length (the strongest signal, ahead of vocabulary), `**Bold lead.**` openers on every bullet, see-saw pairs, the same rhetorical move repeated across sections, rhetorical-question openers, rule-of-three padding, em-dash overuse, and the AI vocabulary set (delve, leverage, robust, seamless, testament to, showcase, foster). Removal is half of it — prose with every tell stripped and no voice put back reads as a press release, which is its own tell.

This command is the single largest rewriter of README prose in the plugin, so the pass is not optional here and it is not "if time allows": a sync that rewrites six sections and skips the audit ships six sections of machine-shaped prose to the one page players read. State in the Step 5 report that the pass ran and what it changed.

## Step 5 — Report

Print a summary:
- Files updated (with line-count delta per file)
- **The README de-AI pass** — that it ran, and what it changed. If `README.md` was not touched this run, say so; skipping the pass because nothing changed is correct, skipping it silently is not
- Files unchanged (already accurate)
- **Dead exports flagged** (separate section — these are NOT auto-removed; the user decides)
- **Comment citations**, split into applied-after-confirmation and declined-or-unresolved, and the fact that each applied one was comment-only
- Anything you couldn't reconcile (e.g. ambiguous intent, missing context) — flag for the user
- A reminder to review the diffs before committing

## Hard rules

- **Don't invent features.** If the README claims a feature you can't find in code, ASK before deleting — it might be intentional/aspirational. The README's **bundled-library inventory** is not covered by this rule: `documentation-§1` states its removal as a MUST NOT, so it comes out without asking (keeping any genuinely external credit as `## Credits`) — see the README bullet in Step 5.
- **Don't add documentation for things the user didn't document.** If there's no "Configuration" section currently, don't add one.
- **Don't bump the version.** Even if you find drift in version numbers, do NOT change `## Version:` in the TOC, the `VERSION` constant in code, or the README badge URL. Changing the version is `/wow-addon:bump-version`'s job.
- **Don't auto-delete dead exports.** Surface them; the user decides.
- **Documentation only, with exactly one named exception: a confirmed comment-only comment-citation correction.** This command rewrites docs; it does not otherwise edit `.lua`, `.xml`, `.toc`, `.luacheckrc` or `.pkgmeta`. The one exception is the Step 2 comment-citation check, and it is fenced on all four sides — **this check only** (never any other drift the command notices in code), **comments only** (a string literal, a key or a value is reported, never edited), **explicit confirmation every time** (an unanswered prompt is a decline), and **never a guessed target** (the user names the replacement or the item stays flagged). The rule's purpose is intact: this exception cannot reach a line that runs. `/wow-addon:revendor-standards` carries the same boundary for standards citations; the two are written to match, and if they ever disagree, that is the bug.
- **Never edit `libs/`, `Libs/` or `tests/_kit/`.** They are vendored payloads and must stay byte-identical to their upstream tag — a comment defect in there is fixed upstream and re-vendored, never patched in place.
- **Don't hand-edit a generated doc.** The automated-test record and `docs/test-cases.md` are produced by tools, not written. Report staleness; never edit the numbers, and never run `lizard` here — the complexity report's checkpoint is **release**, and it MUST NOT gate a commit (`performance-§10`).
- **Don't invent a dependency.** Every `DEPENDENCIES.md` entry traces to something in this repo. If you suspect a requirement but cannot evidence it, say so in words or leave it out.
- **Don't touch LICENSE, CHANGELOG.md, TODO.md, or any file that isn't a project doc.**
- **Don't commit.**

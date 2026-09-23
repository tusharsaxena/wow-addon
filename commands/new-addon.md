---
description: Scaffold a new Ka0s WoW addon that is born compliant with the Ka0s WoW Addon Standard. Fetches the NEW_ADDON.md playbook + the standards context pack from the WowAddonStandards repo at runtime and follows them to the letter — Ace3 skeleton, the modular layout, MIT, the root doc set (README.md, the CLAUDE.md stub, DEPENDENCIES.md), the canonical docs/ trio (ARCHITECTURE.md, testing.md, smoke-tests.md) and the first automated-test bundle. The context pack is read at runtime and never written into the addon.
argument-hint: <AddonName> [one-line description]
allowed-tools: [Read, Glob, Grep, Bash, Write, WebFetch]
---

Scaffold a new WoW addon named **$ARGUMENTS** in the current working directory, **born compliant** with the Ka0s WoW Addon Standard. You do not carry the scaffolding rules yourself — the canonical rules and the new-addon procedure live in the `WowAddonStandards` repo and evolve there. Fetch the current playbook and context pack, then **follow them to the letter**.

**CRITICAL — the context pack is never stored in the addon.** You fetch `NEW_ADDON_CONTEXT.md` to a scratch path and build from it. Creating `docs/agent-context.md` — under that name or any other — is a compliance failure (`documentation-§3`, anti-pattern #49). The addon's `docs/` holds the canonical trio `ARCHITECTURE.md`, `testing.md` and `smoke-tests.md`, the five **verification-and-record** docs — the generated `test-cases.md`, `performance.md`, `perf-analysis/README.md`, `automated-tests/README.md` and the generated `automated-tests/RESULTS.md` — and the **six unconditional Tier 1 topic-detail docs** `scope.md`, `module-map.md`, `schema.md`, `settings-panel.md`, `data-flow.md`, `common-tasks.md`, plus whatever Tier 2 triggers have fired and any Tier 3 docs the addon needs (`documentation-§3`); the root `CLAUDE.md` stub is the repo's only agent brief.

## `.gitattributes` — the first file, before anything else

**Write the root `.gitattributes` before you write any other file in the new repo** (`line-endings`,
and step 0 of the fetched `NEW_ADDON.md`). Take the **client-bound** body verbatim from the fetched
`line-endings-§5` — or the context pack's `### .gitattributes` starter snippet, which is the same text
— rather than composing one: the `* text=auto eol=crlf` pin, the `*.sh text eol=lf` carve-out, and the
`binary` markings. A new addon is always the client-bound kind.

It goes first because it is the one file whose cost grows with everything already committed.
Retrofitted later it needs `git add --renormalize .` plus a whole-tree re-checkout, and that diff
touches every line of every straggler — the sort of diff that gets approved rather than read. Written
first, every commit after it is correct by construction. **Do not stop at the `*.sh` line**: a
`.gitattributes` holding the carve-out with no pin above it is explicitly not compliance
(`line-endings-§1`), and it is how one repo in this collection reached 111 of 185 tracked text files
disagreeing with the collection's intent while looking handled in review. Add `- .gitattributes` to
`.pkgmeta`'s `ignore:` block — it is dev-only (`packaging`).

## Automated test records — scaffold them with the addon

A new addon is born having adopted `automated-tests`. Before the first commit:

1. Vendor `tests/_kit/` whole-folder from the `LibKa0s` release the **root `CLAUDE.md`** provenance
   line names — `Bundles [LibKa0s](https://github.com/tusharsaxena/LibKa0s) vX.Y.Z (MIT).`, in
   `CLAUDE.md` and **not** `README.md` since LibKa0s v1.8.1 / test-kit revision 9, with no fallback —
   it now carries `run-automated-tests.sh` — then set its executable bit **in the git index**, not
   just in the working tree:

   ```sh
   chmod +x tests/_kit/run-automated-tests.sh
   git update-index --chmod=+x tests/_kit/run-automated-tests.sh
   git ls-files -s tests/_kit/run-automated-tests.sh   # MUST print mode 100755
   ```

   `chmod` alone is not enough and in this collection does nothing at all: every repo sits on a WSL
   **DrvFs** mount that reports every file as `rwxrwxrwx`, so the bit always looks set, and every repo
   has **`core.fileMode=false`**, so git ignores the working tree's mode even when it does change. The
   mode that survives a clone is the one git recorded, so `git ls-files -s` reporting `100755` — not
   `100644` — is the only check worth making (`automated-tests-§2`).
2. Confirm the `.gitattributes` you wrote as the repo's **first** file (above) carries
   **`*.sh text eol=lf`**. Do not "add a line to `.gitattributes`" as if the file appeared from
   nowhere — the whole file is a first-commit artifact, and the carve-out is one clause of it.
   `line-endings-§3` requires that line **unconditionally, in both repo kinds**, so do not justify it
   with a collection-wide "everything else here is CRLF" — that is false of the repos which ship
   nothing to the client. What is true and sufficient: a shebang followed by CRLF makes the kernel
   look for an interpreter literally named `bash\r`, and the vendored runner is then broken on every
   checkout. Take the wording from the fetched section, not from this summary.
3. **Wire the kit's two own suites into `tests/run.lua`.** Vendoring lands them; it does not turn
   them on, and `Kit.assertSuiteInventory` scans `tests/_kit/` as well as `tests/`, so a scaffold
   that skips this is born **red** naming the entries to add. That is the intended failure: a gate
   that arrives silently and runs nothing is worse than no gate.

   ```lua
   Kit.run{ dir = "tests/", suites = {
     "test_schema", ...,
     { name = "test_eol",   dir = "tests/_kit/" },   -- line-endings-§7
     { name = "test_prose", dir = "tests/_kit/" },   -- localization-§5, kit revision 24+
   } }
   ```

   `test_prose` is the US-English gate. **Do not hand-write one** — `localization-§5` makes the
   kit's copy the SHOULD precisely because eleven hand-written copies are eleven chances to carry a
   subset, and a subset is a gate whose green means nothing. A new addon has no legacy copy to keep,
   so it takes the kit's and writes none of its own.

   A new addon normally needs **no** `tests/prose_waivers.lua`. Write one only when a scanned file
   legitimately holds a British spelling that is not the addon's English to correct — a library's
   field name, a Blizzard token matched verbatim, a generated dump of the client's own strings — and
   then per **file** and per **word**, with the reason beside it, never per file alone. The three
   MUSTs governing a waiver are in `localization-§5`; take them from the fetched section.

4. Create `docs/automated-tests/README.md` (what it is, how to run it, which suites gate) — and write
   its "what gates, and what only records" section, plus `docs/testing.md`'s gate table, so each states
   **both checkpoints**: `lint` and `tests` gate the **commit**, `perf` and `complexity` never fail a
   **run** and never gate a commit, and the **release** (the tag) is gated on all four suites plus zero
   functions above CCN 15, evaluated by `/wow-addon:bump-version` from the run's `manifest.json`. Take
   the wording from the fetched `automated-tests-§3` — including its release-gate subsection — not from
   this summary and not from the context pack's one-line version. A gate sentence that names no
   checkpoint is the drift `/wow-addon:revendor-standards` sweep 3f exists to clean up; a new addon
   should not be born needing it.
5. Run `~/.claude/wow-addon/bin/ka0s-bounded tests/_kit/run-automated-tests.sh` once, which writes the first bundle and creates
   `RESULTS.md`.

`docs/complexity.md` is **retired** (standard v2.19.0) — do not scaffold one. Neither is
`docs/file-index.md` or `docs/conventions.md` (retired v2.23.0).

## Scaffold the full `docs/` tier model (documentation-§3)

**All six Tier 1 docs are unconditional and ship at v0.1.0**, under exactly these names:
`scope.md`, `module-map.md`, `schema.md`, `settings-panel.md`, `data-flow.md`, `common-tasks.md`.
Write each one **short** rather than deferring it — the tier model's value is that the same question
has the same filename in every repo, and a slot left "for when there's more to say" is a slot the
next agent fills with a name of its own. That is precisely how the collection ended up with five
filenames for the core pipeline and three for the SavedVariables shape.

Then evaluate each **Tier 2** trigger against the code you just generated — count `NS.COMMANDS`,
count distinct messages, read `core/Compat.lua` — and either ship the doc or record a *Not
applicable* row carrying the trigger. A fresh addon normally ships none of Tier 2 and records six
rows; that is the compliant state, not an omission.

Finally write `docs/ARCHITECTURE.md`'s **`## Documentation map`** — the tenth mandated section —
listing every `.md` under `docs/` in exactly one of its four tables — Required, Conditional, **Verification and record** (the six record docs, which sit outside the tier model) and Addon-specific. Write it now, while you still
know why each file exists; it is the register `/wow-addon:standards-audit` reads. Keep
`ARCHITECTURE.md` a **hub**: under ~400 lines, with any section past ~60 lines spilled into its
canonical topic doc behind a summary and one link.

## `docs/smoke-tests.md` — the non-English-client step ships with the scaffold

**A new addon is born with a locale step, not with a smoke doc that is silent about locale.** Write one
numbered step into `docs/smoke-tests.md` covering a deDE/frFR client, and give it a row in the doc's
index table so it is findable by someone planning client time rather than only by someone reading all
of it.

It is scaffolded rather than left to the first person who trips over it because the headless harness
structurally cannot see this class of bug. The base mock's globals are enUS, so a path that keys off a
localized string is green in the suite whether it is right or wrong — the test and the bug agree.
All eleven addons in this collection now carry a locale step (a `locales/` folder loaded from the TOC,
re-measured 2026-09-22) — but the step being present is not the step being right, and the two addons
whose code is most locale-sensitive are still where the worked examples come from.
`LootHistory/core/Compat.lua:194-201` hard-codes the English
wordings — `WARBAND_LINES`, `BIND_TO_WARBAND_PREFIX`, `UE_LITERAL = "until equipped"` — as the fallback
for when the client leaves the `ITEM_ACCOUNTBOUND*` globals nil, reaches them at `:213-214` and `:237`,
and the
same file calls the tooltip "the ONLY witness" for items whose bind type lies; its cases assert against
those literals (`tests/test_compat.lua:62-65` passes `"Auction House"` and `"Auction won: %s"`).
PrettyChat's entire function is overwriting localized `_G` chat format strings across 4957 lines of
loaded source, against a 120-line `locales/enUS.lua`. Neither gap was visible from inside either repo's
green suite, and neither was found by a review that ran per-addon.

**Write the body from the addon's own seams, not from a template.** The step is unconditional; what it
looks at is whatever the addon you just scaffolded actually touches. Enumerate these while you still
have the code in front of you:

- anything reading a localized `_G` — chat format strings, `ITEM_*` and tooltip constants, mail
  subjects, spec and class display names;
- anything matching or parsing a **tooltip line** rather than an API return;
- anything keying off a display string where a numeric id exists — `subType` instead of
  `classID`/`subClassID` is the collection's worked example;
- anything writing a **header, token or key another tool parses**, which must be locale-independent by
  construction and needs the step to say so and prove it.

Where the addon has none of those, the step still ships and says what it checked and why it came back
empty. "This addon reads no localized global" is a claim the next agent can re-check; an absent step is
not.

**Each step names its failure, not only its pass.** A step whose only outcome is "it works" is
unfalsifiable in a client the operator booted specially. Write the concrete symptom: an English
sentence rendered on a German client, a stray `%d` or `%s` conversion artifact left by a format string
that did not match, a bind type that fell back to the English literal and misclassified, a row that
came back `(none)` where the enUS client fills it.

**Say when it can be signed off without the client.** A step that needs a language pack and offers no
alternative is skipped forever, which is how the gap gets recorded as coverage. State which headless
cases stand in for it and which of the numbered sub-steps are sufficient on English —
`ConsumableMaster/docs/smoke-tests.md` § 3c does exactly this, and `KickCD/docs/smoke-tests.md:229`
§ 9b is the shape for a step where the client genuinely is the only witness. Copy the shape from those
two; do not invent a third.

## Standards source

The living standard lives at `https://github.com/tusharsaxena/WowAddonStandards`. Read its files from the raw base:

```
RAW=https://raw.githubusercontent.com/tusharsaxena/WowAddonStandards/master
```

## Step 0 — Resolve the playbook and the context pack (do this first)

Fetch these **faithfully** (see the fetch rule below), in order:

1. `$RAW/NEW_ADDON.md` — the new-addon playbook. It is authoritative for *how the addon is scaffolded*: its numbered steps (however many it now carries), the identity defaults, and the hard rules.
2. `$RAW/standards/NEW_ADDON_CONTEXT.md` — the full context pack: kickstart walkthrough, the modular starter tree, the starter snippets, hard-rules cheat sheet, and the Definition-of-Done checklist. It is the **source of detail** for every starter, including the setup files that wire the shared library modules — read the snippets from the pack rather than inventing them, and do not restate them here. **It is scaffolding you read, not a file you ship** — it is never written into the new addon (see the CRITICAL note above).
3. `$RAW/standards/STANDARDS.md` — the standard's **entry point / index**, fetched when a step references a rule you need to satisfy precisely. Follow its **Sections** list to the specific section file (`$RAW/standards/standards/<file>.md`) on demand. **Don't hard-code section filenames — discover them from the index.** The only fixed paths are `NEW_ADDON.md`, `standards/NEW_ADDON_CONTEXT.md`, and `standards/STANDARDS.md`; everything else you reach by following links, so the standard can be re-organized without changing this command.

**Faithful-fetch rule.** Use `curl -fsSL "<url>"` via Bash and read the saved file — this preserves the document verbatim, which matters most for `NEW_ADDON_CONTEXT.md` since you build the starters from its snippets verbatim. Do **not** rely on WebFetch as the primary path: its summarizer rewrites and truncates content, so the snippets you copy into code would be corrupted. WebFetch is a last-resort fallback only if `curl` is unavailable, and then treat its output as lossy. Save fetched docs under a scratch path (e.g. `/tmp` or the session scratchpad), then `Read` them.

**Hard stop.** If you cannot resolve `NEW_ADDON.md` **and** `standards/NEW_ADDON_CONTEXT.md` (no network, repo moved, 404), do not improvise a scaffold from memory. Stop and tell the user exactly which fetch failed and what you tried — the whole point is to be born compliant with the *current* standard.

**Referencing rule.** The standard cites sections as `filename-§N` (a whole section is its bare filename, e.g. `documentation`; a subsection is `documentation-§1`). Use that form; the retired global `§N.M` notation is gone.

## Step 1..N — Follow NEW_ADDON.md

Once fetched, **execute `NEW_ADDON.md`'s steps exactly as written**, scaffolding into a new `<AddonName>/` folder at cwd (bail with an error if it already exists). Do not restate or reinterpret them here — the fetched playbook is authoritative and may have evolved past this file. As of this writing it directs you to:

1. **Scaffold the skeleton** — the Ace3 stack (AceAddon registration, AceDB saved variables), the modular folder layout, MIT `LICENSE`, and an AceConsole slash command.
2. **Work from the context pack — never write it into the repo.** `standards/NEW_ADDON_CONTEXT.md` is *scaffolding*: read it from your scratch copy, build from it, and leave it there. Do **NOT** create `docs/agent-context.md` or any other stored copy of it (`documentation-§3`, anti-pattern #49) — every question it answers is answered the moment the addon exists, and a stored copy loads as *working context*, so a stale one gets **followed**. The addon's `docs/` carries the canonical trio — `ARCHITECTURE.md`, `testing.md`, `smoke-tests.md` — the five verification-and-record docs (`test-cases.md`, `performance.md`, `perf-analysis/README.md`, `automated-tests/README.md`, `automated-tests/RESULTS.md`) and the six Tier 1 topic-detail docs (`scope.md`, `module-map.md`, `schema.md`, `settings-panel.md`, `data-flow.md`, `common-tasks.md`); the only agent brief in the repo is the short root `CLAUDE.md` **stub** (see `documentation`), with the durable per-addon context in `docs/ARCHITECTURE.md`, `docs/testing.md` and the root `DEPENDENCIES.md`. **Root ships exactly three docs plus `LICENSE`, and never a fourth: the full `README.md`, the `CLAUDE.md` stub, and `DEPENDENCIES.md`** — `DEPENDENCIES.md` is a **root** file, not a `docs/` member.
3. **Lay out files** — use the single modular layout (`core/ modules/ defaults/ settings/ locales/`) for every addon regardless of size (a small addon just has thin folders). Copy the vendored Ace3 `libs/` set you actually `LibStub()` from an existing Ka0s addon so versions stay consistent. Then vendor the **two Ka0s-owned payloads** from the `LibKa0s` repo itself — never from a sibling addon's copy, which may already have drifted:
   - its inner `LibKa0s/` folder → the new addon's `libs/LibKa0s/`, copied **whole**, and TOC-listed as the single aggregate `.xml` line the library ships. Copy every module, including ones the first release won't wire — a partial copy is the forbidden case, and it fails two ways: a module missing its dependency never registers at all (silently absent), while a module whose shell arrived without its attach file constructs fine and dies at **call** time, a panel build later.
   - its root-level `testkit/` folder → the new addon's `tests/_kit/`. It is a **sibling** of the ship folder, not inside it, and it goes under `tests/` — **never** `libs/`, which is the ship payload.
4. **Fill in the starters** — TOC (fixed field order + `#`-section file listing), including the `## X-Standard:` line pointing at the standards repo; entry file, compat shims, locale, database/migrations, schema-driven settings, and the message bus — from the context pack's starter snippets.

   **The shared subsystems are consumed, not written.** The prefixed chat printer, the shared art and type, the debug console, the options panel toolkit, the slash dispatcher and the performance harness are `LibKa0s` modules. A new addon is born with **one setup file per adopted module**, and each holds exactly two things: a **descriptor** (the addon's seams into its own state — where a value lives, not how it looks) and a **degradation stub** for when the library is absent. Nothing else. Hand-building any of them — a private console, a private widget-maker set, a private dispatcher, a private test framework — is the forking anti-pattern the standard forbids outright, and so is patching the vendored copy instead of pushing an **additive** field upstream.

   **The art is already in the payload, so use it.** `LibKa0s-Media-1.0` ships the icon catalog, the monospace face and the bar textures inside `libs/LibKa0s/media/`, which the whole-folder copy in step 3 already brought in. A new addon is therefore born able to draw the collection's marks and has no reason to ship art of its own beyond its logo: wire `core/MediaSetup.lua` **first** of the setup files (`core/Constants.lua` resolves its font path from the seam that file publishes), draw window close controls through the **one** `NS.MakeCloseButton` wrapper the addon defines in `core/CoreSetup.lua` — never a bare two-argument call to the factory, anywhere, decoration hooks handed to a shared module included; the dropped third argument silently yields the fallback glyph, and because a texture path that is never built draws nothing and raises nothing, no lint run, test or smoke check can see it (this has shipped twice in the collection) — give a title-bar control strip and any modal catalog marks, and put a mark **beside** a wide action button's label rather than instead of it. Every call takes the addon's own **folder name** — the library is vendored and cannot know which folder it landed in, and a wrong texture path draws nothing and raises nothing. A mark the catalog lacks is added **upstream** in the `LibKa0s` repo by the generator that produced the rest, never drawn one-off into the new addon. The settings panel is deliberately out of scope for now.

   The playbook names the setup files, their TOC positions and the descriptor fields each one carries, and the context pack carries the snippets. Follow those; don't reconstruct them from this file. Two invariants worth carrying into every one of them: each stub **MUST** answer every member the addon actually calls (a stub missing one is a crash moved to a rarer code path, not a fallback), and a stub **MUST NOT** re-implement the library's formatters, line formats, color codes or layout constants — that copy is the one that goes stale.
5. **Write tests first** — stand up `tests/` on the **vendored** `tests/_kit/` harness (thin extender over its base mock, load list derived from the TOC) and drive behavior test-first. Test what is **yours** — the descriptors, the degradation stubs, the addon's own logic — and do not re-test the library's internals; those cases live in the library repo, and a second copy is exactly the duplication this arrangement exists to remove.
6. **Write the README to `documentation-§1`'s canonical structure**, and **run the de-AI pass over it before the first commit.** `documentation-§1` MUSTs a **de-AI writing pass** on every `README.md` edit (anti-pattern #77): run the `/humanize` skill, or audit against a published AI-writing pattern catalogue, and fix what it finds **before** the change is committed. A brand-new README is the case the rule exists for: every word of it was just generated, with no human draft underneath, so it carries the tells at full strength. It binds this file only — the `CLAUDE.md` stub, `DEPENDENCIES.md` and the `docs/` trio are contributor surfaces and are exempt. What the pass looks for, so it is not a vibe check: uniform paragraph and sentence length (the strongest signal, ahead of vocabulary), `**Bold lead.**` openers on every bullet, see-saw pairs, the same rhetorical move repeated across sections, rhetorical-question openers, rule-of-three padding, em-dash overuse, and the AI vocabulary set (delve, leverage, robust, seamless, testament to, showcase, foster). Removal is half of it — prose with every tell stripped and no voice put back reads as a press release, which is its own tell. Take the section order and every template from the fetched playbook, and note three things it now states which older Ka0s READMEs get wrong, because a scaffold that copies an existing addon's README inherits all three:
   - **The standard badge is NOT a link.** Write the bare image — `![Standard](https://img.shields.io/badge/Ka0s-WoW_Addon_Standard-yellow)` — never wrapped in `[…](https://github.com/tusharsaxena/WowAddonStandards)`. `_`, not `%20`. The standards-repo reference that binds the addon lives in the two places `documentation-§6` makes normative and a reader can act on: the TOC `## X-Standard:` field and the root `CLAUDE.md` `## Standards compliance (read first)` section. The badge's job on a page written for players is to *declare*, not to navigate.
   - **The README MUST NOT carry a bundled-library inventory** — no `## Libraries`, `## Bundled libraries`, `## Libraries and credits`, `## Credits and libraries`, `## Credits and bundled libraries`, and no library roll-call smuggled into the intro prose. The Ace3 / LibSharedMedia / LibDataBroker / LibDBIcon list, the "everything ships inside the addon, nothing else to install" library paragraph and the `LibKa0s` provenance sentence all stay out. Which libraries a build vendors is a **contributor** fact with two homes that are already read by the people it is for: root `DEPENDENCIES.md` (`documentation-§7`) and `docs/ARCHITECTURE.md` (`documentation-§3`).
   - **`## Credits` is optional and external-only** (`documentation-§1` item 13) — third-party artwork, a font, a sound pack, another author's work. It is the **last** section, after `## Version History`. A new addon with nothing external to credit ships no `## Credits` section at all.

   And the playbook's **step 6a**, which is a `CLAUDE.md` edit rather than a README one and is therefore the step most easily lost: **write the `LibKa0s` provenance line into the root `CLAUDE.md` stub** — `Bundles [LibKa0s](https://github.com/tusharsaxena/LibKa0s) vX.Y.Z (MIT).`, naming the **exact tag** both vendored payloads (`libs/LibKa0s/` and `tests/_kit/`) were copied from in step 3. Not the README. The consumer-side vendored-payload gate (`tests/test_vendor_sync.lua`, `testing-§11`) reads this line out of `CLAUDE.md` — since LibKa0s v1.8.1 / test-kit revision 9, with **no fallback to `README.md`** — so a scaffold that omits it, or writes it to the README, is born red rather than born compliant. The line moves in the same commit as the bytes, in both directions.
7. **Write the root `DEPENDENCIES.md`** — the toolchain contract (`documentation-§7`). Every piece of software needed to build, run, test or release *this* addon, split **runtime (in-game) / development / release-and-assets**, each entry carrying the **evidence** for it (the TOC's dependency fields, a script's import, the command the harness runs) — never what a new addon usually needs, because one speculative entry costs the reader's trust in the whole list. Copy-pasteable WSL2 / Ubuntu install commands plus a one-line verification per tool. A new addon's honest runtime section is normally "World of Warcraft (Retail); nothing else", since every library is vendored. It answers *what to install*; `docs/testing.md` answers *how to verify* — point at it rather than restating it.
8. **Produce the first automated-test bundle** — run the vendored `tests/_kit/run-automated-tests.sh` through `~/.claude/wow-addon/bin/ka0s-bounded` and commit the frozen `docs/automated-tests/<YYYYMMDD-HHMMSS>/` bundle plus the first `RESULTS.md` row (`automated-tests-§1`, `automated-tests-§4`), **before** tagging `v0.1.0`. That bundle's `complexity.txt` is the first `lizard` report and `RESULTS.md` carries the watch list; there is **no** `docs/complexity.md` (retired, v2.19.0). Take the invocation from the fetched section rather than from memory and run it **verbatim**, because the record's whole value is that later releases can be diffed against this one. `lint` and `tests` gate the commit; `perf` and `complexity` only record there — but the **tag** is gated on all four plus zero functions above CCN 15, so `v0.1.0` waits on a green run of every suite. If a tool is not installed, that suite is a **skip with its reason** — never a pass, and never a fabricated number, and a skip is not a pass for the release gate either.
9. **Check the Definition of Done** before tagging `v0.1.0`.
10. **Register in the roster** — add the addon's row to `standards/ADDONS.md` in the `WowAddonStandards` repo. Note that this edit is in a *different* repo; if you can't push there, tell the user this row still needs adding rather than silently skipping it.

Use the identity defaults from the playbook (Author `add1kted2ka0s` / Ka0s, MIT, Ace3, Retail-only single `## Interface:`, TOC `Title: Ka0s <Human Name>`, `<Addon>DB` saved-vars, 2–3 lowercase-char slash, PascalCase folder). Where the playbook says the context pack is the source of detail, read the snippet from the pack rather than inventing one.

If this list and the fetched `NEW_ADDON.md` ever disagree, **the fetched playbook wins**; where the playbook defers to `STANDARDS.md` (and its section files) / the context pack, those win.

## After scaffolding, print

- The created file tree (just the paths), including the **root** doc set — `README.md`, the `CLAUDE.md` stub and `DEPENDENCIES.md`, plus `LICENSE`, and nothing else at root — `docs/` (the trio — ARCHITECTURE.md, testing.md, smoke-tests.md — the five verification-and-record docs: test-cases.md, performance.md, perf-analysis/README.md, automated-tests/README.md, automated-tests/RESULTS.md — and the six Tier 1 topic-detail docs: scope.md, module-map.md, schema.md, settings-panel.md, data-flow.md, common-tasks.md; **no** complexity.md, **no** agent-context.md, **no** file-index.md, **no** conventions.md), the vendored `libs/LibKa0s/`, and `tests/_kit/`.
- **Whether the first automated-test bundle was actually produced**, by which invocation, and which suites ran versus skipped with their reasons — or, if the runner could not run, that the bundle is still owed and the addon must not be tagged until it exists.
- **Which `LibKa0s` modules the scaffold wired** (one setup file each) versus which were vendored but not yet wired — adoption is per module and on the addon's own schedule, so "vendored, not wired" is a normal state, not an omission. Say where each payload was copied **from** (the `LibKa0s` repo, not a sibling addon) and **at which tag**, and confirm that tag is what the root `CLAUDE.md` provenance line names — that line, not the README's, is what the vendored-payload gate reads.
- The exact `## Interface:` value used and where it came from.
- The exact `## X-Standard:` URL written into the TOC.
- A reminder to run the packager (or fetch libs) before first use if `libs/` was left empty, and — if step 8's roster row could not be added from here — that `standards/ADDONS.md` still needs the new row.

Do not create `git init`, CI files, or hooks unless the user asks or the playbook requires them.

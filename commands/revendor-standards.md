---
description: Refresh an addon's in-repo reference to the Ka0s WoW Addon Standard so its documentation matches the current upstream standard — the three-place standards reference (TOC X-Standard, README badge, CLAUDE.md "Standards compliance"), plus retired notation, retired file names and unresolvable section references swept out of the whole repo, excluding libs/, tests/_kit/ and the frozen docs/audits/, docs/reviews/ and docs/automated-tests/ bundles. Documentation only, and never writes the standard's text into the repo; a citation sitting in a code or config comment is reported and corrected only on confirmation, comment-only. Defaults to the repo at cwd; pass repos or `all` to sweep siblings.
argument-hint: [path | repo names | all]
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion]
---

Refresh the **in-repo reference to the Ka0s WoW Addon Standard** in the addon(s) in scope, so the documentation an agent loads as working context matches the standard as it exists **today**. Scope comes from `$ARGUMENTS` (see Step 1); with no arguments this is the repo at cwd.

## What this is, and what it is not

The standard evolves upstream. An addon that was compliant when it was written keeps a *snapshot* of that standard in its docs — the `X-Standard:` line, the README badge, the `CLAUDE.md` compliance section, and every doc sentence that names a section, counts a doc set (root or `docs/`) without naming its members, or cites a file the standard has since retired. None of that goes red. No test covers a doc, lint does not read prose, and a stale brief does not go quiet — it is loaded as working context and gets **followed**. This command is the sweep that closes that gap.

Three commands touch the same doc set from different directions; keep them apart:

- **`/wow-addon:standards-audit`** measures the addon against the standard and writes a frozen `docs/audits/<date>/` bundle. It is **read-only** and produces findings. This command is not an audit: it produces no bundle, no deviation IDs, and no severity ratings, and it **edits**.
- **`/wow-addon:sync-docs`** reconciles the docs against the addon's **own code**. It owns count claims, slash parity, dead exports, doc scaffolding, and the migrate-and-delete flow for `docs/agent-context.md`.
- **This command** reconciles the docs against the **current upstream standard text**. Where the two overlap, `sync-docs` owns anything requiring code analysis; this one owns anything requiring the fetched standard.

**"Revendor" here means the *reference*, never a copy — with exactly one exception.** Do not write the standard's rules, its section files, or the scaffolding context pack into the addon under any name. A stored copy of the standard's *rules* is the same failure as a stored context pack (`documentation-§3`, anti-pattern #49) — it describes the standard on the day it was copied, forever, and because it sits inside the repo it wins over the live document for every agent that reads it. What lives in the addon is a **pointer** plus the small canonical block the standard itself says to carry.

The exception is the **quirks catalogue** (Step 3d). It is not a rule and not scaffolding — it is reference data about the game client, and a working addon needs it at hand, offline, next to the code that works around it. It is carried as a **vendored block**, under the same discipline as `libs/LibKa0s/`: copied whole, replaced wholesale, never patched locally, and stamped with the version it came from. Keep the two straight — the rules are pointed at, the catalogue is vendored — because relaxing the first rule to accommodate the second is how a whole copy of the standard ends up in a repo.

## Standards source

The living standard lives at `https://github.com/tusharsaxena/WowAddonStandards`. Read its files from the raw base:

```
RAW=https://raw.githubusercontent.com/tusharsaxena/WowAddonStandards/master
```

## Step 1 — Establish the scope, and never guess it

Decide **which repos** before touching anything. The failure mode is asymmetric: too narrow leaves a repo carrying a stale brief that keeps teaching the old rule, while too wide rewrites the working context of a repo nobody asked you to open — and an edit to `CLAUDE.md` is not something the user notices in a diff they were not expecting.

Proceed **unasked** only when the answer is certain:

- `$ARGUMENTS` names repos, a path, or `here` — obey it verbatim.
- `$ARGUMENTS` is empty — the scope is the repo at **cwd**, and only that repo. Never widen on your own initiative; a sibling repo being equally stale is not evidence the user meant it.

`$ARGUMENTS` of `all` means the sibling repos next to this one. Do **not** treat that as blanket approval: build the candidate list, print for each candidate what this run would change (file, item, before → after in one line), and **ask before the first edit**. The same holds for any multi-repo scope — with more than one repo in scope, nothing applies silently.

Identify a candidate as a Ka0s addon by finding a `.toc` at its root. A directory with no TOC is **skipped with the reason printed**, not guessed at — this command edits `CLAUDE.md` and `README.md`, filenames common enough that a wrong directory is a real risk.

Do **not** consult `standards/ADDONS.md` to build the scope. The roster names addons that exist; it does not say which ones this user wants edited right now, and a roster-driven sweep would reach repos the session never touched.

## Step 2 — Resolve the standard (do this before reading any repo doc)

Fetch these **faithfully** (see the fetch rule below), in order:

1. `$RAW/standards/STANDARDS.md` — the standard's **entry point / index**. Read its version/date line at the top and hold it; the report cites it.
2. **Every section file the `STANDARDS.md` Sections list links.** Discover them by following the Sections links and fetch each `$RAW/standards/standards/<file>.md`. **Do NOT hard-code section filenames.** The set of section files, and their names, is exactly the kind of thing that changes upstream — and this command's job is to notice that change in a repo's docs, which it cannot do from a hard-coded list that changed at the same time. The only fixed path is `standards/STANDARDS.md`.
3. Any further file those reference and you need — follow the links under `STANDARDS.md`'s "Related documents", on demand.

**Faithful-fetch rule.** Use `curl -fsSL "<url>"` via Bash and read the saved file — this preserves the document verbatim, which matters here more than almost anywhere: you are copying the standard's **canonical wording** into a repo's `CLAUDE.md`, so a summarizer's paraphrase becomes that repo's permanent instruction to every future agent. Do **not** rely on WebFetch as the primary path; it is a last-resort fallback only if `curl` is unavailable, and then treat its output as lossy and **ask before writing any canonical block sourced from it**. Save fetched docs under a scratch path (e.g. `/tmp` or the session scratchpad), then `Read` them.

**Hard stop.** If you cannot resolve `standards/STANDARDS.md` **and** the section files it lists (no network, repo moved, 404), stop and tell the user exactly which fetch failed and what you tried. Do **not** refresh anything from memory. This command's whole output is text written into the one document every future agent loads first; refreshing it from a half-read or remembered standard is strictly worse than leaving the old text alone, because the old text at least was correct once and is dated by its own staleness.

**Referencing rule.** The standard cites sections as `filename-§N` — a whole section is its bare filename (e.g. `documentation`, `anti-patterns`), a subsection is `filename-§N` (e.g. `documentation-§6`). Use that exact form in everything you write; the retired global `§N.M` notation is gone, and putting it back is one of the drifts this command exists to remove.

## Step 3 — Build the refresh inventory (per repo, read-only)

Read the repo's doc set: root `README.md`, root `CLAUDE.md` (and `CLAUDE.*.md` variants), root `DEPENDENCIES.md`, every `docs/*.md` (including `docs/perf-runs/README.md`), and the `.toc` file(s) — the TOC only for its `## X-Standard:` field. Then inventory drift across six areas. **One of them, 3b, reads wider than the doc set** — a standards citation is bound wherever the repo authored it, so that sweep covers code, tests and config too, under its own edit boundary. Everything else here stays inside the doc set.

Two artifacts in that set are **generated**, not prose: `docs/test-cases.md` and the automated-test record (`docs/automated-tests/RESULTS.md` and the frozen per-run bundles; a standalone `docs/complexity.md` is **retired** as of standard v2.19.0 — finding one is a pre-adoption finding to report, not a doc to sync). Read them for stale *references* only — a retired notation or a dead section name in their headers is fair game — and never touch their numbers. A hand-edited complexity report is worse than an absent one, because it reads as measured (`performance-§10`, anti-pattern #51).

### 3a. The three-place standards reference (`documentation-§6`)

The standard requires the reference in **all three** places; a repo missing any of them is non-compliant (anti-pattern #34). Read `documentation-§6` from the fetched section file — it is authoritative for the list and the canonical wording, and it may have moved past what is written here. As of this writing:

1. **TOC `## X-Standard:`** — must carry the standard's repo URL (`toc-file-§1`). Check presence, exact field spelling, and that the URL matches the standard's current home.
2. **README standard badge** — the badge/line linking the standard in the README badge row (`documentation-§1`). Check presence and URL. Note that `documentation-§1` forbids percent-escaped spaces in badge URLs and angle-bracket placeholders in shipped README content — if the badge you would write or repair trips either rule, write the compliant form.
3. **`CLAUDE.md` → `## Standards compliance (read first)`** — the agent-facing directive. Check that the section exists under that heading and that its **substance** matches the canonical wording: the addon is built to the standard, the standard is the source of truth, and — the load-bearing part — a change that would deviate makes the agent **stop and flag** it rather than silently deviate *or* silently conform, leaving the user to classify it as an accepted deviation or an upstream change to the standard.

The canonical block is **adapt-the-name, keep-the-substance**. A repo that renamed `<Name>` or reflowed the paragraphs is fine. A repo whose version has lost the stop-and-flag directive, dropped the two-way classification, or softened "MUST" into a suggestion has drifted in the way that matters, because that directive is the entire mechanism keeping the collection converged — record it as drift.

### 3b. Retired and unresolvable references, swept out of the whole repo

**Scope: the whole repo, not just `docs/`.** A standards citation is bound by `documentation-§6` ("Citing the standard") wherever the repo authored it — code comments, `.luacheckrc` and `.pkgmeta` headers, test files, `docs/` pages alike. Scoping this sweep to `docs/` is why most surviving retired notation lives in code: it was never looked at. Grep the whole repo and record each hit with `file:line`:

```sh
grep -rEn '§[0-9]+\.[0-9]' . \
  --exclude-dir=.git --exclude-dir=libs --exclude-dir=_kit \
  --exclude-dir=audits --exclude-dir=reviews --exclude-dir=automated-tests
```

**Five paths are excluded, and each for its own reason.** Read `documentation-§6` from the fetched section file for the authoritative list; as of this writing:

- **`libs/`** — vendored payload. It is not this repo's authored text, and patching it locally is the vendoring failure `3d` describes at length.
- **`tests/_kit/`** — the vendored test kit, same rule.
- **`docs/audits/`**, **`docs/reviews/`** and **`docs/automated-tests/`** — **frozen evidence**, all three. A bundle records what was true on its date against the standard of its date; its notation is part of what it recorded. **`docs/automated-tests/` is the one that gets forgotten, and it is not a rounding error**: in one roster addon, 30 of its 69 `§N.M` lines live inside frozen automated-test bundles (`test-cases.md` and `tests.txt` under three run stamps), so a sweep that omits this exclusion "finishes" only by corrupting three bundles. Those 30 are evidence and are **expected to survive**.

`--exclude-dir` matches by directory **basename**, so `_kit`, `audits`, `reviews` and `automated-tests` are excluded wherever they sit rather than only at their canonical path. That is intended — but it also means the exclusion list is coarser than the five paths it stands for, so state the command you ran in the report and let the count be reproducible rather than asserted.

Then inventory these forms:

- **Global `§N.M` notation** (e.g. `§4.2`, `Section 12.1`) → the `filename-§N` scheme. `documentation-§6` grades this a **SHOULD**: it is uniformly wrong in a way a machine sweeps mechanically, which is what this command is. Resolve each old reference to the section it actually means by reading the fetched section files; if a reference cannot be resolved with confidence, flag it for the user rather than guessing a target.
- **Section filenames that no longer exist upstream** — any doc citing a section file not in the fetched Sections list. Renamed sections get rewritten to the new name; genuinely deleted ones are flagged.
- **Out-of-range and malformed `filename-§N` references** — the **MUST-fix** half of `documentation-§6`, and the reason this command range-checks rather than just rewrites. A retired `§N.M` at least tells the reader "this is old"; these send the reader to a section that does not exist while looking perfectly current.
  - **Malformed** — anything that does not parse as `filename-§N` at all: an empty or non-numeric N (`slash-commands-§:`, `foo-§`, `foo-§a`), an abbreviated filename (`perf-§2` for `performance`), a `STANDARDS.md` reference carrying a number.
  - **Out-of-range** — the section file exists but has no such section: `options-ui-§41` against a file that carries §1–§11.
  - **Range-check it, don't eyeball it.** Step 2 already fetched every section file, so this command holds exactly the data needed. For each fetched `<file>.md`, count its **local** `§`-numbered headings (the `### N.` subsection headings the file's own numbering uses — count them, don't infer from the largest number you see, since a renumbering gap is itself the defect). Hold `{filename → highest local N}`. Then extract every `filename-§N` reference the sweep found and flag any whose filename is unknown, whose N exceeds that file's count, or whose N does not parse.
  - **Report these individually, never rolled up.** The `§N.M` sweep is one line with the command and the count (`documentation-§6`'s reporting shape); these are few and each needs a decision, because the correct target is not mechanically derivable — a citation numbered past the end of a file could mean the section moved, was deleted, or was a typo for a different file. Flag with `file:line`, the reference as written, and the file's real range. **Do not guess a target.**
- **A doc set stated as a count without its members** — "the four canonical docs", "the quartet", "the three root docs", or any count that leaves a slot open. This is the specific failure that reconstructs a deleted file from memory: a model that reads "quartet", counts three names and supplies the fourth produces exactly one answer, and it is the forbidden one. Rewrite to name the members inline, in both places a count is now made:
  - **Root** — the full `README.md`, the `CLAUDE.md` stub, and `DEPENDENCIES.md`, plus `LICENSE` (`documentation`, `documentation-§7`).
  - **`docs/`** — the canonical trio `ARCHITECTURE.md`, `testing.md`, `smoke-tests.md`; the five verification-and-record docs `test-cases.md`, `performance.md`, `perf-runs/README.md`, `automated-tests/README.md`, `automated-tests/RESULTS.md`; and the six unconditional **Tier 1** topic-detail docs `scope.md`, `module-map.md`, `schema.md`, `settings-panel.md`, `data-flow.md`, `common-tasks.md`, plus whatever **Tier 2** triggers have fired and any **Tier 3** docs the addon ships (`documentation-§3`). A standalone `complexity.md` is **not** a member — retired in v2.19.0 — and neither is `file-index.md` or `conventions.md`, retired in v2.23.0. Text calling the topic-detail docs "optional" or saying they "vary per addon and are not fixed by the standard" is the **pre-v2.23.0 wording** and is rewritten: the tier is fixed, the content is per-addon.
- **The retired "drop-in" label** for the scaffolding context pack, and any live imperative to copy the pack's contents into `docs/` — that instruction *is* the forbidden file in everything but name, so an agent following it ships the file without ever reading the name. Rewrite to fetch-and-discard wording.

Sweep hits are the fetched standard's current vocabulary applied to this repo's prose — do not invent a rename the standard has not made, and do not touch quoted historical text inside `docs/audits/`, `docs/reviews/` or `docs/automated-tests/` (see the hard rules).

#### The edit boundary, now that the sweep reaches code

Widening the *scope* does not widen the *permission*. Sort every 3b hit by where it lives, and treat the two halves differently:

- **A hit in `docs/`, the README, `CLAUDE.md` or any other prose file** — applies automatically, exactly as before. Nothing about doc handling changes.
- **A hit in `.lua`, `.xml`, `.toc`, `.luacheckrc`, `.pkgmeta` or any other code or config file** — is **reported with `file:line`, listed in the Step 4 inventory, and applied only on the user's explicit confirmation**. When they confirm, the edit is **comment-only**: it changes the text of a comment or a commented header line and nothing else. If correcting a reference would require touching a line that is not a comment — a string literal, a key, a value — do not edit it; report it and say why.

This is a deliberate, narrow relaxation of this command's blanket "never edit code" rule, and it is written as an exception in the hard rules rather than left to be inferred, because the rule and this behaviour would otherwise contradict each other. The rule exists so an agent authorized to rewrite every repo's `CLAUDE.md` cannot also reach into `.lua`; a confirmed comment-only correction of a citation the standard MUSTs or SHOULDs is the one case where the rule's purpose and its letter come apart. It stays narrow: this sweep only, comments only, confirmation always, and never in a multi-repo run without the whole plan confirmed up front (Step 4).

### 3c. `CLAUDE.md` pointer list and the `docs/` shape

- The `CLAUDE.md` pointer list **MUST NOT** name a file the standard forbids (`documentation-§2`). Record any such pointer, and any pointer to a file that does not exist in the repo.
- Verify **root** against the standard's root doc set — the full `README.md`, the `CLAUDE.md` stub and `DEPENDENCIES.md`, plus `LICENSE` (`documentation-§7`). A missing `DEPENDENCIES.md`, or a fourth doc sitting at root, is recorded.
- Verify `docs/` against the canonical set — `ARCHITECTURE.md`, `testing.md`, `smoke-tests.md`; the five verification-and-record docs `test-cases.md`, `performance.md`, `perf-runs/README.md`, `automated-tests/README.md` and `automated-tests/RESULTS.md`; the six **Tier 1** docs `scope.md`, `module-map.md`, `schema.md`, `settings-panel.md`, `data-flow.md` and `common-tasks.md`; plus fired **Tier 2** triggers and any **Tier 3** docs (`documentation-§3`). A surviving `docs/complexity.md`, `docs/file-index.md` or `docs/conventions.md` is a **pre-adoption finding to report**, never a missing member to create — and so is a Tier 1/2 subject filed under a non-canonical name (`data-model.md`, `saved-variables.md`, `pipeline.md`, `settings-system.md`, `wow-quirks.md`, `slash-commands.md`, `debug-console.md`, …): report the rename, do not perform it.
- **Flag missing members; do not create them** — root and `docs/` alike. Writing an `ARCHITECTURE.md` requires reading the addon's code, which this command does not do; a `DEPENDENCIES.md` must be **evidence-based** (`documentation-§7`), which means reading the scripts, the harness and the TOC, and a speculative one costs the reader's trust in the whole list; and the automated-test record is produced by running the vendored runner, which this command does not run. An empty or invented one is worse than an absent one — `/wow-addon:sync-docs` owns the scaffolding, and the record is regenerated at release by `/wow-addon:bump-version`.

### 3d. The vendored quirks catalogue

The standard carries a **quirks catalogue** — client behaviors the collection discovered the hard way, promoted upstream by `/wow-addon:harvest-standards` so no addon pays the discovery cost twice. Find that section through the fetched Sections list; **never hard-code its filename**. If the standard has no such section yet, skip this step entirely and say so — there is nothing to vendor, and inventing a catalogue from this repo's own notes is the harvest command's job, in the other direction.

The addon's quirks file is **two parts**, and the split is the whole design:

```markdown
<!-- BEGIN VENDORED: quirks catalogue v2.17.1 (source: WowAddonStandards) -->
… the upstream catalogue, whole …
<!-- END VENDORED -->

## <Addon>-specific quirks

… findings not yet promoted upstream, plus genuine one-repo residue …
```

- **Replace the vendored block wholesale.** Same rule as `libs/LibKa0s/`: whole payload, never a subset, never a local patch. A local edit inside the markers is reverted silently by the next revendor, and the behavior it fixed comes back as a regression with **no cause in this repo's history** — the exact failure the vendoring discipline exists to prevent. If a repo has edited inside the markers, do not merge it: report the edit verbatim, tell the user it belongs in the addon's own section (where `harvest-standards` will find it and promote it), and overwrite only once they have somewhere to put it.
- **Stamp the block with the catalogue's version.** This is the one place a standard version *does* belong in the repo — a vendored payload with no source version cannot be told stale from current, which is why LibStub minors exist. It does not contradict the no-version-stamp rule in Step 5: that rule governs the **reference**, which points at a live document and is dated by its own staleness; this is a **copy**, which is not.
- **Prune what has been promoted.** Any quirk in the addon's own section that now appears in the vendored block is duplicated — the upstream version won, and it is usually the deeper write-up, since the harvest promotes the deepest of several independent discoveries. Remove the addon's copy and say which entries you removed. Two live copies of one finding is how they diverge.
- **Never touch the addon's own section otherwise.** Everything below the end marker belongs to the repo. It is the harvest's input, and editing it here would let this command launder its own text into the next harvest's evidence.
- If the file does not exist and the standard has a catalogue, **creating it is one of the mechanical items** — a vendored block plus an empty addon section is complete and correct, and unlike an `ARCHITECTURE.md` it requires no knowledge of this addon's code.

### 3e. `docs/agent-context.md` — report, do not delete

If the file exists (under that name or any other stored copy of the context pack), record it as a compliance failure (`documentation-§3`, anti-pattern #49) and **point the user at `/wow-addon:sync-docs`**, which owns the migrate-then-delete flow: salvage anything genuinely addon-specific into `docs/ARCHITECTURE.md` or the `CLAUDE.md` stub, then delete. Do not delete it here and do not migrate from it here. Two specs owning one destructive action is how the migration half gets skipped and real content is lost.

You **may** still fix references *to* it — a `CLAUDE.md` pointer naming it is 3c drift — but say plainly in the report that the file itself is still there and which command removes it.

### 3f. Normative claims the standard has since changed

3b sweeps forms the standard has **retired**. This sweep is the other half: a doc sentence that still *paraphrases correctly-named rules the standard has since rewritten*. It is scoped narrowly and deliberately — to statements about **which checkpoint gates on what** — because that is where the collection's docs are one template with nine copies, and because the rewrite is fully determined by the fetched section rather than by judgement.

Read `automated-tests-§3` ("What gates, and what only records", including its release-gate subsection) from the fetched section file and hold its current wording. Then check these locations, by name:

- **`docs/testing.md`** — its `Gates?` table (the per-suite yes/no column) **and** its "Commits are gated on…" paragraph.
- **`docs/automated-tests/README.md`** — the section headed "What gates, and what only records", including its per-suite rows.
- **root `CLAUDE.md`** — any sentence of the form "complexity — recorded, never a gate", or the same claim about `perf`.

The drift is always the same shape: a **gate statement that names no checkpoint**. `automated-tests-§3` gates lint and tests at the **commit**, and gates all four suites plus zero functions above CCN 15 at the **release**, so a bare "perf and complexity never fail a run" is now only half true and reads as the whole truth. Rewrite so every gate statement names its checkpoint — for example "…never fail a **run** and never gate a **commit**; the **tag** is gated on all four suites plus zero functions above CCN 15, evaluated by `/wow-addon:bump-version` from the run's `manifest.json`". Take the wording from the fetched section, not from this example, and change nothing about a sentence that already qualifies its checkpoint.

Record each hit with `file:line` like any other sweep item. A doc that already names both checkpoints is not a hit — do not rewrite prose that is already correct.

**One statement of this claim is out of this sweep's reach, and the report must say so.** The lead-in paragraph of `docs/automated-tests/RESULTS.md` is **generated** — the vendored runner writes it on every run (`tests/_kit/run-automated-tests.sh`, from `LibKa0s`'s `testkit/`). Editing it here would be reverted by the next run, and the record is generated besides (Step 3's note, and the hard rule below). Fixing it means re-vendoring a corrected runner from `LibKa0s` and re-running. So the report **MUST** state plainly that the `RESULTS.md` lead-in is runner-generated, that this sweep did not touch it, and that it is fixed upstream — a report that lists three fixed locations and stays silent about the fourth reads as having finished the job.

## Step 4 — Show the inventory, then apply

Print the inventory before writing anything, grouped by repo and file, one line per item:

```
STANDARDS REFRESH — KickCD (standard v2.18.0, 2026-08-04)

KickCD.toc
  MISSING: ## X-Standard: line absent (documentation-§6 #1, anti-pattern #34)

README.md
  STALE:   standard badge URL uses %20 escapes (documentation-§1)

CLAUDE.md
  DRIFT:   "Standards compliance (read first)" lost the stop-and-flag directive (documentation-§6 #3)
  ORPHAN:  pointer list names docs/agent-context.md

docs/ARCHITECTURE.md
  RETIRED: cites §4.2 → architecture-§5 (line 31)
  RETIRED: "the canonical quartet" → name the members inline (line 88)

docs/testing.md
  CHANGED: Gates? table and "Commits are gated on…" state no release checkpoint (automated-tests-§3, line 24)

CODE / CONFIG — comment-only, needs your confirmation before anything is written
  core/Constants.lua:11        RETIRED:  cites §3.4 → architecture-§4
  settings/Slash.lua:199       MALFORMED: "slash-commands-§:" — no section number at all
  settings/OptionsSetup.lua:43 OUT-OF-RANGE: "options-ui-§41" — options-ui.md carries §1–§11
  .luacheckrc:1                RETIRED:  cites §7.2 → testing-§7
  Notation sweep: 39 hits, from
    grep -rEn '§[0-9]+\.[0-9]' . --exclude-dir=.git --exclude-dir=libs --exclude-dir=_kit \
      --exclude-dir=audits --exclude-dir=reviews --exclude-dir=automated-tests
    (30 further hits live inside frozen docs/automated-tests/ bundles and are excluded as evidence)

FLAGGED (not changed here)
  docs/automated-tests/RESULTS.md lead-in states the same gate claim, but it is runner-generated
    (tests/_kit/run-automated-tests.sh) — out of this sweep's reach; fixed by re-vendoring a
    corrected runner from LibKa0s and re-running
  docs/agent-context.md exists — run /wow-addon:sync-docs to migrate and delete it
  docs/smoke-tests.md absent — canonical member missing; /wow-addon:sync-docs scaffolds it
  DEPENDENCIES.md absent at root — required by documentation-§7 (anti-pattern #50); it must be
    written from this repo's own evidence, so /wow-addon:sync-docs owns it, not this command
  docs/automated-tests/RESULTS.md absent — required by automated-tests-§4; regenerated at release by
    /wow-addon:bump-version, never written here
```

Then apply:

- **Apply automatically, in prose files only** — the mechanical items, where the correct output is fully determined by the fetched standard and no repo prose is lost: the `X-Standard:` URL (adding the field in its correct TOC position, or correcting it), the README badge URL, notation and filename rewrites, retired-label rewrites, **the 3f checkpoint-qualification rewrites** (the correct sentence is fixed by `automated-tests-§3`; a gate statement gains its checkpoint and loses nothing the repo wrote), and **adding** a missing `## Standards compliance (read first)` section verbatim from the canonical wording.
- **Ask first** — anything that overwrites the repo's own words. Replacing prose in an existing `Standards compliance` section that has drifted, rewriting a sentence whose intended meaning is ambiguous, and any retired-notation hit whose target you could not resolve with confidence. Show the before and after and let the user decide.
- **Ask for every code and config hit, always** — every 3b hit outside a prose file, however mechanical it looks. Present the whole `CODE / CONFIG` block, confirm once, then apply **comment-only** edits (see 3b, *The edit boundary*). No confirmation, no edit: an unanswered prompt is a decline, not a default. Out-of-range and malformed references are shown with the reference as written and the file's real section range, and are **not** rewritten to a guessed target even after confirmation — the user names the target or the item stays flagged.
- **Ask for everything** when more than one repo is in scope. In a multi-repo run nobody is watching each repo, so nothing applies silently there — confirm the whole plan up front, then run it.

Use `Edit` for surgical changes. Only `Write` a whole file when adding one that does not exist, which for this command means nothing under `docs/`.

**Preserve line endings.** Detect each file's existing endings (LF or CRLF) and write the same. The plugin's CRLF hook covers `.gitattributes`-declared CRLF repos, but writing the right ending first keeps the diff to the lines that actually changed.

## Step 5 — Report

Per repo:

- Files changed, with a line-count delta each.
- Items applied, items deferred by the user, and items **flagged for another command** (with the command named).
- Anything you could not reconcile — an unresolvable section reference, a doc whose intent was ambiguous — stated plainly rather than resolved by guess.
- **The 3b sweep's command and its count**, verbatim, so the number is reproducible rather than asserted (`documentation-§6`'s reporting shape) — one rolled-up line for the retired-notation half, plus the exclusions and, where any exist, how many hits were left standing inside frozen `docs/audits/`, `docs/reviews/` and `docs/automated-tests/` bundles **on purpose**. A count with no stated scope is not a count.
- **Every out-of-range and malformed reference, individually**, whether it was corrected or left flagged — these are `documentation-§6`'s MUST-fix half and the one part of this sweep that never rolls up.
- **Every code or config hit**, split into applied-after-confirmation and declined, and the fact that each applied one was comment-only.
- **Whenever 3f changed anything**: the sentence that the `docs/automated-tests/RESULTS.md` lead-in carries the same gate claim, is **runner-generated**, was therefore **not** swept, and is fixed by re-vendoring a corrected `tests/_kit/run-automated-tests.sh` from `LibKa0s` and re-running. Say it even when the repo's `RESULTS.md` is currently absent.

Then, once for the run:

- **The standard version resolved** — the version and date from the top of `STANDARDS.md` (e.g. `v2.17.1, 2026-08-03`), so the run is reproducible.
- A reminder to review the diffs and commit. This command does not commit.

**Do not write the standard version into any repo file — except the vendored quirks block's own stamp (Step 3d).** A version stamp attached to the *reference* is a fact that goes stale the moment the standard moves, silently and invisibly, so it belongs in the run's report where it is read once, at the moment it is true. A version stamp attached to a *vendored copy* is the opposite: it describes the copy, which genuinely is that version, and without it nobody can tell a current block from a stale one.

## Hard rules

- **Documentation only, with exactly two named exceptions.** Never edit `.lua`, `.xml`, or any code. The exceptions are:
  1. The `.toc`'s `## X-Standard:` field — documentation living in metadata. Leave every other TOC field alone.
  2. **A 3b standards-citation correction, in a comment, after the user confirms it.** A citation is bound by `documentation-§6` wherever the repo authored it, including code and config, so the sweep must be able to see those files; this exception is what lets it also fix them, and it is fenced on all four sides — **this sweep only** (never any other drift this command notices in code), **comments only** (a string literal, a key or a value is reported, never edited), **explicit confirmation every time** (silence is a decline, and a multi-repo run confirms the whole plan up front), and **never a guessed target** for an out-of-range or malformed reference. Everything else in code stays untouched and gets reported. The rule's purpose — that an agent licensed to rewrite every repo's `CLAUDE.md` cannot also reach into `.lua` — is intact: this exception cannot reach a line that runs.
- **Never write the standard's rules into the repo.** No copy of `STANDARDS.md`, no section files, no context pack, under any name. What lives in the addon is the reference, the canonical `CLAUDE.md` block the standard itself prescribes, and the vendored quirks block — that block is the *only* upstream text carried in, and it is carried whole or not at all.
- **Never merge inside the vendored quirks markers.** Replace the block wholesale; a local edit found inside it is reported and relocated to the addon's own section, never quietly preserved and never quietly overwritten.
- **Never edit the addon's own quirks section.** It is `/wow-addon:harvest-standards`' input; the only change permitted below the end marker is removing an entry that has since been promoted upstream, which is reported.
- **Never create missing `docs/` members, and never create a missing root `DEPENDENCIES.md`.** Flag them; `/wow-addon:sync-docs` scaffolds them from the repo's own evidence.
- **Never hand-edit the automated-test record or `docs/test-cases.md`.** They are generated. Correcting a retired section reference in their header text is allowed; touching a number is not, and a hand-edited complexity report reads as measured when it is not (`performance-§10`, anti-pattern #51). This command does not run `lizard`.
- **Never delete `docs/agent-context.md`.** Report it and name the command that removes it.
- **Never touch `docs/audits/<date>/`, `docs/reviews/<date>/` or `docs/automated-tests/<stamp>/`.** All three are frozen history — they record what was true on their date, against the standard of their date, and rewriting their notation falsifies the record. This holds even when they use retired forms; that is what a dated artifact is *for*. **All three are excluded from the 3b sweep, and the third is the one that gets forgotten**: one roster addon carries 30 `§N.M` lines inside its automated-test bundles, so a sweep that reaches zero without this exclusion reached zero by corrupting evidence. If a repo's notation count will not go to zero, check what the surviving hits are *in* before assuming the sweep is unfinished.
- **Don't bump the version, don't commit, don't push.** Version bumping is `/wow-addon:bump-version`'s job; pushing is `/wow-addon:finalize`'s alone.
- **Don't sync docs against code.** Count claims, slash parity, dead exports and module maps are `/wow-addon:sync-docs`'s. If you notice such drift, mention it in the report and name that command; do not fix it here.
- **Never hard-code a section filename.** Discover every one from the fetched `STANDARDS.md` Sections list.
- If this file and the fetched standard ever disagree about what the reference must contain, **the fetched standard wins**.

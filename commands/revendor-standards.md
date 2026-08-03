---
description: Refresh an addon's in-repo reference to the Ka0s WoW Addon Standard so its documentation matches the current upstream standard — the three-place standards reference (TOC X-Standard, README badge, CLAUDE.md "Standards compliance"), plus retired notation and retired file names swept out of docs/. Documentation only; never touches code, never writes the standard's text into the repo. Defaults to the repo at cwd; pass repos or `all` to sweep siblings.
argument-hint: [path | repo names | all]
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion]
---

Refresh the **in-repo reference to the Ka0s WoW Addon Standard** in the addon(s) in scope, so the documentation an agent loads as working context matches the standard as it exists **today**. Scope comes from `$ARGUMENTS` (see Step 1); with no arguments this is the repo at cwd.

## What this is, and what it is not

The standard evolves upstream. An addon that was compliant when it was written keeps a *snapshot* of that standard in its docs — the `X-Standard:` line, the README badge, the `CLAUDE.md` compliance section, and every doc sentence that names a section, counts the canonical `docs/` set, or cites a file the standard has since retired. None of that goes red. No test covers a doc, lint does not read prose, and a stale brief does not go quiet — it is loaded as working context and gets **followed**. This command is the sweep that closes that gap.

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

Read the repo's doc set: root `README.md`, root `CLAUDE.md` (and `CLAUDE.*.md` variants), every `docs/*.md`, and the `.toc` file(s) — the TOC only for its `## X-Standard:` field. Then inventory drift across five areas.

### 3a. The three-place standards reference (`documentation-§6`)

The standard requires the reference in **all three** places; a repo missing any of them is non-compliant (anti-pattern #34). Read `documentation-§6` from the fetched section file — it is authoritative for the list and the canonical wording, and it may have moved past what is written here. As of this writing:

1. **TOC `## X-Standard:`** — must carry the standard's repo URL (`toc-file-§1`). Check presence, exact field spelling, and that the URL matches the standard's current home.
2. **README standard badge** — the badge/line linking the standard in the README badge row (`documentation-§1`). Check presence and URL. Note that `documentation-§1` forbids percent-escaped spaces in badge URLs and angle-bracket placeholders in shipped README content — if the badge you would write or repair trips either rule, write the compliant form.
3. **`CLAUDE.md` → `## Standards compliance (read first)`** — the agent-facing directive. Check that the section exists under that heading and that its **substance** matches the canonical wording: the addon is built to the standard, the standard is the source of truth, and — the load-bearing part — a change that would deviate makes the agent **stop and flag** it rather than silently deviate *or* silently conform, leaving the user to classify it as an accepted deviation or an upstream change to the standard.

The canonical block is **adapt-the-name, keep-the-substance**. A repo that renamed `<Name>` or reflowed the paragraphs is fine. A repo whose version has lost the stop-and-flag directive, dropped the two-way classification, or softened "MUST" into a suggestion has drifted in the way that matters, because that directive is the entire mechanism keeping the collection converged — record it as drift.

### 3b. Retired forms, swept out of every doc

Grep the repo's docs for forms the standard has retired and record each hit with `file:line`:

- **Global `§N.M` notation** (e.g. `§4.2`, `Section 12.1`) → the `filename-§N` scheme. Resolve each old reference to the section it actually means by reading the fetched section files; if a reference cannot be resolved with confidence, flag it for the user rather than guessing a target.
- **Section filenames that no longer exist upstream** — any doc citing a section file not in the fetched Sections list. Renamed sections get rewritten to the new name; genuinely deleted ones are flagged.
- **The canonical `docs/` set stated as a count without its members** — "the four canonical docs", "the quartet", or any count that leaves a slot open. This is the specific failure that reconstructs a deleted file from memory: a model that reads "quartet", counts three names and supplies the fourth produces exactly one answer, and it is the forbidden one. Rewrite to name the members inline (`ARCHITECTURE.md`, `testing.md`, `smoke-tests.md`, plus the generated `test-cases.md` and any topic-detail docs).
- **The retired "drop-in" label** for the scaffolding context pack, and any live imperative to copy the pack's contents into `docs/` — that instruction *is* the forbidden file in everything but name, so an agent following it ships the file without ever reading the name. Rewrite to fetch-and-discard wording.

Sweep hits are the fetched standard's current vocabulary applied to this repo's prose — do not invent a rename the standard has not made, and do not touch quoted historical text inside `docs/audits/` or `docs/reviews/` (see the hard rules).

### 3c. `CLAUDE.md` pointer list and the `docs/` shape

- The `CLAUDE.md` pointer list **MUST NOT** name a file the standard forbids (`documentation-§2`). Record any such pointer, and any pointer to a file that does not exist in the repo.
- Verify `docs/` against the canonical set — `ARCHITECTURE.md`, `testing.md`, `smoke-tests.md`, plus the generated `test-cases.md` and topic-detail docs. **Flag missing members; do not create them.** Writing an `ARCHITECTURE.md` requires reading the addon's code, which this command does not do — an empty or invented one is worse than an absent one, and `/wow-addon:sync-docs` owns that scaffolding.

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

## Step 4 — Show the inventory, then apply

Print the inventory before writing anything, grouped by repo and file, one line per item:

```
STANDARDS REFRESH — KickCD (standard v2.17.1, 2026-08-03)

KickCD.toc
  MISSING: ## X-Standard: line absent (documentation-§6 #1, anti-pattern #34)

README.md
  STALE:   standard badge URL uses %20 escapes (documentation-§1)

CLAUDE.md
  DRIFT:   "Standards compliance (read first)" lost the stop-and-flag directive (documentation-§6 #3)
  ORPHAN:  pointer list names docs/agent-context.md

docs/ARCHITECTURE.md
  RETIRED: cites §4.2 → architecture-§5 (line 31)
  RETIRED: "the four canonical docs" → name the trio inline (line 88)

FLAGGED (not changed here)
  docs/agent-context.md exists — run /wow-addon:sync-docs to migrate and delete it
  docs/smoke-tests.md absent — canonical member missing; /wow-addon:sync-docs scaffolds it
```

Then apply:

- **Apply automatically** — the mechanical items, where the correct output is fully determined by the fetched standard and no repo prose is lost: the `X-Standard:` URL (adding the field in its correct TOC position, or correcting it), the README badge URL, notation and filename rewrites, retired-label rewrites, and **adding** a missing `## Standards compliance (read first)` section verbatim from the canonical wording.
- **Ask first** — anything that overwrites the repo's own words. Replacing prose in an existing `Standards compliance` section that has drifted, rewriting a sentence whose intended meaning is ambiguous, and any retired-notation hit whose target you could not resolve with confidence. Show the before and after and let the user decide.
- **Ask for everything** when more than one repo is in scope. In a multi-repo run nobody is watching each repo, so nothing applies silently there — confirm the whole plan up front, then run it.

Use `Edit` for surgical changes. Only `Write` a whole file when adding one that does not exist, which for this command means nothing under `docs/`.

**Preserve line endings.** Detect each file's existing endings (LF or CRLF) and write the same. The plugin's CRLF hook covers `.gitattributes`-declared CRLF repos, but writing the right ending first keeps the diff to the lines that actually changed.

## Step 5 — Report

Per repo:

- Files changed, with a line-count delta each.
- Items applied, items deferred by the user, and items **flagged for another command** (with the command named).
- Anything you could not reconcile — an unresolvable section reference, a doc whose intent was ambiguous — stated plainly rather than resolved by guess.

Then, once for the run:

- **The standard version resolved** — the version and date from the top of `STANDARDS.md` (e.g. `v2.17.1, 2026-08-03`), so the run is reproducible.
- A reminder to review the diffs and commit. This command does not commit.

**Do not write the standard version into any repo file — except the vendored quirks block's own stamp (Step 3d).** A version stamp attached to the *reference* is a fact that goes stale the moment the standard moves, silently and invisibly, so it belongs in the run's report where it is read once, at the moment it is true. A version stamp attached to a *vendored copy* is the opposite: it describes the copy, which genuinely is that version, and without it nobody can tell a current block from a stale one.

## Hard rules

- **Documentation only.** Never edit `.lua`, `.xml`, or any code. The single exception in the `.toc` is the `## X-Standard:` field, which is documentation living in metadata — leave every other TOC field alone.
- **Never write the standard's rules into the repo.** No copy of `STANDARDS.md`, no section files, no context pack, under any name. What lives in the addon is the reference, the canonical `CLAUDE.md` block the standard itself prescribes, and the vendored quirks block — that block is the *only* upstream text carried in, and it is carried whole or not at all.
- **Never merge inside the vendored quirks markers.** Replace the block wholesale; a local edit found inside it is reported and relocated to the addon's own section, never quietly preserved and never quietly overwritten.
- **Never edit the addon's own quirks section.** It is `/wow-addon:harvest-standards`' input; the only change permitted below the end marker is removing an entry that has since been promoted upstream, which is reported.
- **Never create missing `docs/` members.** Flag them; `/wow-addon:sync-docs` scaffolds them from the code.
- **Never delete `docs/agent-context.md`.** Report it and name the command that removes it.
- **Never touch `docs/audits/<date>/` or `docs/reviews/<date>/`.** Those bundles are frozen history — they record what was true on their date, against the standard of their date, and rewriting their notation falsifies the record. This holds even when they use retired forms; that is what a dated artifact is *for*.
- **Don't bump the version, don't commit, don't push.** Version bumping is `/wow-addon:bump-version`'s job; pushing is `/wow-addon:finalize`'s alone.
- **Don't sync docs against code.** Count claims, slash parity, dead exports and module maps are `/wow-addon:sync-docs`'s. If you notice such drift, mention it in the report and name that command; do not fix it here.
- **Never hard-code a section filename.** Discover every one from the fetched `STANDARDS.md` Sections list.
- If this file and the fetched standard ever disagree about what the reference must contain, **the fetched standard wins**.

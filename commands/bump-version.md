---
description: Bump the addon version to X.Y.Z everywhere it appears — TOC, code constants, README badges, Version History table, CLAUDE*.md — roll the release history for everything since the last tag into the README's "Version History" for an addon (or CHANGELOG.md in a Ka0s-owned library repo, the only place documentation-§1 permits one), and write the release automated-test bundle's ANALYSIS.md and RESULTS.md watch list. Gated: runs the full four-suite battery FIRST and refuses to bump anything unless lint, tests, perf and complexity all pass with zero functions above CCN 15. Asks for the version if not provided.
argument-hint: [X.Y.Z]
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write]
---

Bump the version of the addon in the current working directory.

## Step 1 — Determine the new version

If `$ARGUMENTS` is non-empty and looks like a semver (`X.Y.Z` or `X.Y.Z-tag`), use it as the new version.

Otherwise:
1. Find the current version. Check, in this order: the `.toc` file's `## Version:` line, then any `local VERSION = "..."` / `MAJOR_VERSION` constant in the code, then the README's "Version" mention.
2. Propose a bump:
   - **patch** (`X.Y.Z` → `X.Y.Z+1`): the safe default for bugfixes / small changes
   - **minor** (`X.Y.Z` → `X.Y+1.0`): for new features
   - **major** (`X.Y.Z` → `X+1.0.0`): for breaking changes
   Recommend one with a one-line reason based on what's in the working tree (`git status` / `git diff` if it's a git repo, otherwise a quick scan of recent file mtimes).
3. Ask the user: "Current version is X.Y.Z. Propose bumping to A.B.C ([reason]). Confirm or specify another version."
4. Wait for the user's reply before proceeding.

## Step 2 — The release gate (all four suites; STOP on any failure)

A release is gated on **all four** suites plus **zero functions above CCN 15**
(`automated-tests-§3`, *The release gate*). This runs **before any file is edited**, so a failed gate
leaves the repo exactly as it was found.

This is **not** the commit gate and **MUST NOT** become one. Commits stay gated on lint + the harness
only (`testing-§4`), the runner's own exit code is unchanged, and `perf`/`complexity` still never fail
a run — the threshold lives here, in the release command, read off the manifest the run already
writes. A release has no `--no-verify`, which is exactly why a threshold is safe at this checkpoint
and corrosive at the other one.

1. **Run the full battery**, tagged with the version from Step 1:

   ```sh
   tests/_kit/run-automated-tests.sh --release X.Y.Z
   ```

   Use the **vendored** runner — never the four tools invoked separately, and never a hand-assembled
   equivalent. If the runner is **missing**, the addon has not adopted `automated-tests`: stop, say so,
   and tell the user adoption is its own change. Do not improvise a gate from loose tool invocations.

2. **Evaluate the gate from `docs/automated-tests/<stamp>/manifest.json`** — read the file, do not
   infer from console text. All five conditions must hold:

   | Gate | Condition |
   |---|---|
   | Lint | `suites.lint.status == "pass"` — which already means **0 warnings and 0 errors**, since `luacheck` exits non-zero on either |
   | Tests | `suites.tests.status == "pass"` **and** `suites.tests.failed == 0` |
   | Perf | `suites.perf.status == "pass"` |
   | Complexity | `suites.complexity.status == "pass"` |
   | CCN | `suites.complexity.warnings == 0` — no function above CCN 15 |

3. **A `skip` is not a pass.** A suite that did not run cannot satisfy its gate: a release claiming
   zero CCN > 15 on a run where `lizard` never executed is an unmeasured claim. Report it as
   **NOT EVALUATED** — visibly distinct from FAILED — name the tool and the install command from
   `DEPENDENCIES.md` (`pipx install lizard`, `sudo luarocks install luacheck`, a Lua 5.1 interpreter),
   and stop.

   **One narrow exception:** `perf` skipped because the addon ships no `tests/perf.lua` — nothing was
   there to run. That passes the gate and **MUST** be stated as such in the Step 6 report and the
   release notes. A perf skip for any *other* reason (no interpreter) is NOT EVALUATED and stops.

4. **On any failure or non-evaluation: STOP.** Change nothing — no version string, no README, no
   CHANGELOG, no `RESULTS.md` beyond the row the run itself wrote. Do not tag, do not commit, do not
   push. A partial bump is worse than a clean refusal, because the next attempt starts from a state
   nobody chose.

5. **Report every failed gate, not the first.** Evaluate all five and print the full picture, so a
   release blocked for a lint error that also has four failing tests and a CCN 62 function is
   understood once rather than across three rounds. Use this shape:

   ```
   RELEASE GATE FAILED — version NOT bumped (still X.Y.Z)

   | Gate       | Result       | Detail                                          |
   |------------|--------------|-------------------------------------------------|
   | Lint       | PASS         | 0 warnings / 0 errors in 24 files                |
   | Tests      | FAIL         | 3 failed of 689                                  |
   | Perf       | PASS         | 6 scenarios                                      |
   | Complexity | PASS         | ran; lizard 1.17.31                              |
   | CCN <= 15  | FAIL         | 14 functions over 15, max CCN 33                 |

   Failing tests:
     - <case name>  (tests/test_ledger.lua:212)
     ...
   Functions over CCN 15 (worst first):
     - Database:QueryList  CCN 33  core/Database.lua:90
     ...
   Bundle: docs/automated-tests/<stamp>/  (written; it is the evidence for this refusal)

   Nothing was modified. Fix the above and re-run /wow-addon:bump-version.
   ```

   Name **every** failing test case and **every** function over CCN 15 with its file:line and CCN,
   worst first — a count alone sends the user back to the bundle to find out what to do, and the
   command has already read it.

6. **Only when all five pass**, print a one-line `RELEASE GATE PASSED` with the same table and
   continue to Step 3. The bundle is written either way: it is the evidence for the decision, and a
   refusal with no record is not reviewable.

## Step 3 — Find every version reference

Search the addon root recursively (skip `libs/`, `Libs/`, `.git/`, `node_modules/`) for the **current** version string. Targets to check explicitly (don't rely on the regex search alone for these — verify each):

**Code & TOC**
- `## Version:` line(s) in every `.toc` (including per-flavor variants: `*_Mainline.toc`, `*_Cata.toc`, etc.)
- `VERSION =`, `ADDON_VERSION =`, `MAJOR_VERSION =`, `MINOR_VERSION =`, `version = ` in `.lua`
- Any string literal matching the current semver in `.lua` and `.xml`

**README**
- The "Version" heading or text mention near the top
- **Shields.io badge URLs** that include the version. Common shapes:
  - `https://img.shields.io/badge/version-X.Y.Z-...`
  - `https://img.shields.io/curseforge/v/<id>` (auto-derived — leave alone)
  - `https://img.shields.io/github/v/release/<owner>/<repo>` (auto-derived — leave alone)
  - Manually-pinned badges with the version in the path or `?label=` parameter
- **A `## What's new in X.Y.Z` section — DO NOT create one, and do not roll one forward.** `documentation-§1` dropped it at standard v2.42.0: its content was defined as a copy of the top `## Version History` row, so it could only ever be in sync or in breach. If a README still carries one (or a `## What's New` / `## Latest release` variant), leave it byte-for-byte alone and report it for Step 6 as a `documentation-§1` violation whose fix is deletion — removing it is `/wow-addon:sync-docs`' job, not a release edit.
- **"Version History" table** at the bottom of the README — this lists OLD versions as facts, not "the current version". Add a NEW row for the new version with an auto-generated summary of changes since the last version bump (see Step 3b). Do NOT rewrite existing rows. **The new row's Highlights cell is BULLETED**: every highlight carries a `- ` prefix and highlights are separated by `<br>` (`documentation-§1` item 10, standard v2.55.0), including when there is only one. Markdown renders no `<ul>` inside a table cell, so the literal hyphen is the mechanism. Writing the row unbulleted re-introduces the shape the whole table was just re-punctuated out of, and the next audit reads the new shape as the deviation.
- **Two things in the README this command MUST NOT touch while it is in the badge row.** The **standard badge is not a link** (`documentation-§1`) — it is the bare `![Standard](https://img.shields.io/badge/Ka0s-WoW_Addon_Standard-yellow)`, it carries no version, and it must be left exactly as found: never re-wrapped in `[…](https://github.com/tusharsaxena/WowAddonStandards)` as a tidy-up. And the README carries **no bundled-library inventory** — no `## Libraries`, `## Bundled libraries`, `## Libraries and credits`, `## Credits and libraries`, no library list in the intro prose, and no `Bundles [LibKa0s] …` sentence — so a release never adds one, and never "refreshes" a vendored-library version there. If one exists in the repo, leave it and report it (anti-pattern #58); removing it is `/wow-addon:sync-docs`' job, not a release edit.

**Other docs**
- `CLAUDE*.md` mentions of the version — with one **explicit exception**: the root `CLAUDE.md`'s `LibKa0s` provenance line, `Bundles [LibKa0s](https://github.com/tusharsaxena/LibKa0s) vX.Y.Z (MIT).`. That `vX.Y.Z` is the **vendored library's** tag, not the addon's, and it is the input the consumer-side vendored-payload gate reads (`testing-§11`; it lives in `CLAUDE.md` rather than `README.md` since LibKa0s v1.8.1 / kit revision 9). Rolling it to the addon's new version silently makes the gate compare against a tag the repo never vendored. Leave it alone and report it as "skipped — LibKa0s vendored tag, not the addon's version". It only moves on a re-vendor, in the same commit as the bytes.
- `ARCHITECTURE*.md` mentions
- `CHANGELOG.md` — **only in a Ka0s-owned library repo**, where it gets a full entry for the new release (see Steps 3b and 4). In an **addon** repo `documentation-§1` forbids it at root and this command never writes one; a `CHANGELOG.md` found at an addon root is **reported, not filled** (Step 4). Do NOT rewrite past entries.
- `.pkgmeta` if it pins a version explicitly

**Generated docs (do NOT hand-edit — one gets regenerated in Step 4b)**
- `docs/automated-tests/RESULTS.md` and every `docs/automated-tests/<run>/` bundle — produced by the vendored runner. Never hand-edit a number in either; a fresh record is produced by re-running the tool (Step 4b), and a bundle is frozen once written.
- `docs/test-cases.md` — the generated inventory. Regenerated by the runner, never edited.

**Auto-substituted (do NOT touch)**
- `## Version: @project-version@` (BigWigsMods packager substitution) — leave alone, version comes from git tag at build time
- Auto-derived shields badges (CurseForge, GitHub release) — leave alone
- Note any of these to the user as "skipped because auto-derived"

Report the full list of matches **before** editing.

## Step 3b — Summarize changes since the last release

One pass over the release's changes, written up at **two granularities**:

- **Full list** — every user-relevant change since the last release. Feeds a library repo's CHANGELOG entry (Step 4); in an addon repo it is still collected, because it is what the highlights are drawn from, but it is not written anywhere on its own.
- **Highlights** — the 3–5 changes a user actually cares about. Feeds the README's Version History row (Step 4), where each one is written with a `- ` prefix and joined to the next with `<br>`.

**Determine the "since" reference**, in this order:
1. **The last git tag** — `git describe --tags --abbrev=0` (fall back to `git tag --list --sort=-v:refname | head -1` if the repo has no annotated tags). This is the release boundary; prefer it over everything below.
2. Git tag matching the previous version specifically: `git tag --list 'v<previous>' '<previous>'`.
3. The commit that last set the version constant to the previous value. Find via `git log -G '"<previous>"' -- <files-from-Step-2>` and pick the most recent commit that *introduced* the previous version (typically the previous bump-version commit).
4. The date in the row above the new one in the README's Version History table — use `git log --since=<date>` as a fallback window.
5. If none of the above can be determined, skip the generated content, leave the existing README section and the new row's summary alone, and warn the user that no `since` reference was found. Never invent a change list.

State which reference you used and how many commits it spans before writing anything.

**Collect change material**:
1. `git log <since>..HEAD` — full subjects *and* bodies; bodies carry the "why" for non-trivial commits.
2. `git diff --stat <since>..HEAD` — scope, and a cross-check that nothing sizeable is missing from the log.
3. If a `CHANGELOG.md` exists and has a populated `## [Unreleased]` (or equivalent) section, treat those bullets as **authoritative** change *material* — keep their wording and merge anything from git they don't already cover, rather than rewriting them. Reading it is always allowed; whether anything is written **back** to it is Step 4's repo-kind question, and in an addon repo the answer is no.

**Write the full list** (a library repo's CHANGELOG entry; in an addon, the pool the highlights come from):
- Group by category in this order: **Added**, **Changed**, **Fixed**, **Removed**, **Deprecated**, **Docs**, **Internals**. Skip empty categories.
- Cover every user-relevant change — this list is exhaustive where the highlights are selective.
- Past tense, user-visible language ("Added /foo command", "Fixed taint regression on PLAYER_REGEN_DISABLED") — not commit-message phrasing.
- Roll up genuine trivia (whitespace, lint, formatting, dependency bumps) into a single "Internals" bullet.
- No commit hashes, PR numbers, or author names.

**Write the highlights** (for the README):
- 3–5 bullets, drawn from the full list — the headline features and the fixes users were waiting on. Not a second derivation from git.
- Same past-tense, user-visible voice. One line each, no sub-bullets.
- If the release is purely internal (no user-visible change), say so in one line rather than padding with trivia.
- For the Version History table cell, join the highlight bullets with `<br>` so the cell stays one row. Example: `Added /foo command<br>Fixed taint on combat exit<br>Updated deDE locale`.

## Step 4 — Update

For each match, replace the old version with the new version using `Edit`. Be precise — match the exact context to avoid touching unrelated strings (e.g. don't replace `1.0.0` if it's an Interface number, a library version, or a Lua version requirement).

**Then run the de-AI pass over what you just wrote.** `documentation-§1` MUSTs a **de-AI writing pass** on every `README.md` edit (anti-pattern #77): run the `/humanize` skill, or audit against a published AI-writing pattern catalogue, and fix what it finds **before** the change is committed.

It binds the README alone — the `CHANGELOG.md` entry in a library repo is a contributor-facing file and is exempt — and here it binds the text **this command authored**: the new Version History row's highlights cell, and the perf-skip sentence when Step 2 recorded one. Release-notes bullets are where the tells cluster hardest, because they are generated from a git log: `**Bold lead.**` openers on every bullet, three-item rhythm whether or not the release had three parts, and "significantly improved" where a number belongs. Fix them before the commit, and say in the Step 6 report that the pass ran.

For the README **"Version History" table**: insert a NEW row at the top (or wherever the table is ordered to put the latest), with the new version, today's date if the table has a date column, and the `<br>`-joined highlights in the release-notes cell. Do NOT modify existing rows.

### Where the release history goes: `CHANGELOG.md` is a library file, not an addon file

`documentation-§1` settles this in both directions, and the answer differs by repo kind. **Establish which kind you are in before writing any history**, by the same test the rest of the plugin uses: a **`.toc` at the repo root means an addon**; a Ka0s-owned library repo (`LibKa0s` and its kin — `library-stack-§7`'s applicability list) has none.

**In an addon repo — a root `CHANGELOG.md` is FORBIDDEN.** The player-facing history already has one mandated home, and it is the one this command rolls: the README's `## Version History` table (`documentation-§1`, item 11). A second history is exactly the drift the never-a-fourth-root-doc rule exists to prevent. So:

- **Never create one**, as before.
- **Never fill one that exists**, which is the change. If a root `CHANGELOG.md` is present, leave it byte-for-byte alone and record it for the Step 6 report as a `documentation-§1` violation, naming the fix: fold anything user-facing into `## Version History` and delete the file. Filling it every release is what kept the contradiction alive and invisible — the file stayed current, so nothing ever read as broken.
- **`docs/CHANGELOG.md` is not a compliant relocation** (`documentation-§3`) — it is the same second history one directory down. Report it the same way.
- Do **not** delete it here. This command bumps a version; deleting a root doc is a change the user makes deliberately, and it needs the fold-forward first.

**In a Ka0s-owned library repo — a root `CHANGELOG.md` is REQUIRED**, and this step writes it. `testing-§10`'s versioning suite MUSTs that the changelog account for the version every file is at, and it has nowhere else to look: a library ships no player-facing README with a `## Version History` table to carry the history instead. Write a full entry for this release — `## [X.Y.Z] — YYYY-MM-DD` with today's date, followed by the Step 3b **full list** grouped by category. If an "Unreleased" or `## [Unreleased]` header exists, that entry becomes this one (retitle it and merge its existing bullets in — see Step 3b). Follow the file's established formatting (Keep a Changelog style, link refs at the bottom, etc.) rather than imposing a new one; if the file maintains comparison links, add one for the new version. It stays at **root**, where the versioning suite reads it. Do NOT rewrite past entries.

### The perf-skip exception goes into the release notes, not just the chat

Step 2 item 3 makes it a **MUST** that a `perf` gate satisfied by the no-scenarios exception "be stated as such in the Step 6 report and the release notes" (`automated-tests-§3`). Step 6 is the chat report and it scrolls away; **this** step is the one that authors the release notes, so this is where the obligation is discharged. Do not leave it to Step 6 alone.

When Step 2 recorded the perf gate as passing because **the addon ships no `tests/perf.lua`**, the release notes carry **one sentence** saying so — in whichever release-notes home this repo kind has (see *Where the release history goes*, above):

- in an **addon** repo, the new **`## Version History`** row's highlights cell;
- in a **library** repo, this release's **`CHANGELOG.md`** entry.

Use this substance, adapted to the file's voice:

> Verified against lint, tests and complexity. This addon ships no `tests/perf.lua`, so the perf suite was skipped rather than measured — the release gate covered three suites, not four.

Rules for that sentence:

- **It is a note, not a highlight.** Put it on its own line at the end of whichever body Step 4 wrote — not as one of the 3–5 highlight bullets, and not in the Version History row's `<br>`-joined cell. It describes how the release was *verified*, not what changed since the last one, and Step 3b's rule that every bullet trace to a real commit does not apply to it.
- **Write it only when the exception actually fired.** A release where `perf` ran gets no such sentence; a release where `perf` was NOT EVALUATED never reaches Step 4 at all (Step 2 item 4 stopped it).
- **Only this release's notes.** Past CHANGELOG entries and existing Version History rows are never retro-fitted, per the hard rules — five addons in the collection are permanent perf-skippers and their history stays as written.

## Step 5 — Write up the release run

The bundle already exists: Step 2 produced it, and the gate passed on it. Nothing is re-run here —
re-running would produce a *second* bundle whose numbers are the ones nobody gated on, and two release
bundles for one version is a trend line with a fork in it.

1. **Read the diff against the previous run** — the row above this one in `RESULTS.md` — and write
   the bundle's **`ANALYSIS.md`** to the uniform prompt in the standards repo's `AUTOMATED_TESTS.md`.
   A release run **MUST** carry one (`automated-tests-§5`).

2. **Refresh the `RESULTS.md` watch list**: every function `lizard` warned on and every file in the
   1000–1500 LOC on-notice band, each with a one-line disposition, and anything that **newly** crossed
   marked as such. A regeneration that yields no disposition for what newly crossed has performed the
   ritual and skipped the point (anti-pattern #51).

   After a passing gate the **functions** table reads **"None."** by construction — zero CCN > 15 is
   what the gate enforced. That is a result, not an empty section: write "None." rather than dropping
   the heading. The **files** table is unaffected; the LOC band is not part of the gate, so a file in
   the 1000–1500 band still needs its disposition, and an entry carried as *Accepted* across three
   consecutive release runs is owed a fix or a tracked deviation ID (anti-pattern #53).

3. **Surface the gate result in both places it is owed**, including a `perf` gate satisfied by the
   no-scenarios exception — a release whose perf gate passed because there was nothing to run must say
   so while the user is deciding whether to tag, **and** must say so in the artifact the user still has
   a year later:

   - **Step 4 — the release notes.** This repo kind's release-notes body carries the one-sentence note
     (see Step 4, *The perf-skip exception goes into the release notes*) — the new README `## Version
     History` row in an addon, the `CHANGELOG.md` entry in a library. This is the half `automated-tests-§3`
     MUSTs and the half that is easy to skip, because the chat report feels like it discharged the
     obligation.
   - **Step 6 — the chat report.** Printed beside the gate table while the tag decision is live.

   Neither substitutes for the other.

## Step 6 — Report

Print:
- **`RELEASE GATE PASSED`** with the Step 2 table — lint, tests, perf, complexity, CCN ≤ 15 — and, where the perf gate passed because the addon ships no `tests/perf.lua`, say so plainly rather than letting it read as measured
- Old version → New version
- The `<since>` reference used and the commit count it spanned
- Every file changed (path + the line that was updated)
- Whether a fresh automated-test bundle was produced (with the command run), plus anything that **newly** crossed a threshold and its disposition — or, if `lizard` was absent, that the complexity suite is recorded as a **skip with its reason** and that the release notes should say so. Also report any watch-list entry that has now carried an **Accepted** disposition across three consecutive release runs: it is owed a fix or a tracked deviation ID (`anti-pattern #53`)
- Every version-shaped string found but DID NOT change (with reason — e.g. "looks like a library version, not the addon's version", "auto-derived CurseForge badge", "BigWigsMods @project-version@ substitution")
- **Which repo kind this run treated the repo as** — addon (root `.toc` found, named) or Ka0s-owned library — and, therefore, where this release's history was written: the README's `## Version History` for an addon, `CHANGELOG.md` for a library. One line. It is the premise every history edit above rests on, and getting it wrong is silent.
- **When a root (or `docs/`) `CHANGELOG.md` was found in an addon repo**: state that it was left **untouched**, that it is a `documentation-§1` violation — an addon root ships `README.md`, the `CLAUDE.md` stub, `DEPENDENCIES.md` and `LICENSE`, and the history lives in the README's `## Version History` — and that the fix is to fold anything user-facing into `## Version History` and delete the file. Say it once, plainly, with the path. This command deliberately no longer maintains that file: filling it every release is what let one addon carry a second history for years without anything reading as broken.
- Reminder: tag the commit with `vX.Y.Z` if using the BigWigsMods packager (the packager picks the version up from the latest git tag)

## Hard rules

- **Don't commit.** The user reviews the diffs first.
- **Don't tag.** Tagging is a deliberate user action.
- **Don't create a `CHANGELOG.md` that doesn't already exist, and in an addon repo don't fill one that does.** `documentation-§1` forbids the file at an addon root — the history lives in the README's `## Version History`, which this command rolls. Leave an existing one untouched and report it (Step 6). In a **Ka0s-owned library repo** the file is **required** and this release's entry is written in full (Step 3b's full list). Don't delete an addon's `CHANGELOG.md` here either — the fold-forward comes first and the deletion is the user's.
- **Don't modify existing Version History rows or past CHANGELOG entries** — only add the new version's row/entry.
- **Don't let the generated text outrun the commits.** Every bullet in the CHANGELOG entry and the Version History row must trace to a real change between `<since>` and HEAD. No aspirational or filler entries; if there's nothing since the last tag, say so and bump the version only.
- **Don't let the release notes omit a skipped suite.** When the gate passed because the addon ships no `tests/perf.lua`, Step 4 writes the one-sentence note into this repo kind's release-notes body — the new README `## Version History` row in an addon, the CHANGELOG entry in a library. Printing it in the Step 6 chat report is not enough — the chat is gone by the time anyone reads the release, and notes that say only "verified" over a three-suite gate read as four. This is the mirror of the rule above: that one stops the notes claiming changes that did not happen, this one stops them claiming verification that did not happen.
- **Don't commit a README edit without the de-AI pass.** `documentation-§1` MUSTs it on every `README.md` change (anti-pattern #77), and this command changes one on every run. The release-notes cell it writes is the part to audit; the badges are mechanical.
- **Don't bump the Interface version.** That's `/wow-addon:bump-interface`.
- **Don't hand-edit an automated-test record.** Produce it with the vendored runner. Never write a number into a bundle and never edit a bundle once written — the bundle is the evidence the gate was decided on, including when it refused.
- **Don't bump anything when the Step 2 gate fails.** No version string, no README, no CHANGELOG, no tag, no commit, no push. Report every failed gate with its detail and stop. Never "bump anyway and note it" — a release the gate refused is not a release with a caveat.
- **Don't move the gate to commit time, and don't edit the vendored runner to implement it.** The runner is shared with the commit gate; a threshold inside it would fire on every commit, which is the `--no-verify` failure the standard refuses (`automated-tests-§3`). Read the manifest here instead.
- **Don't re-run the battery in Step 5.** Step 2's bundle is the release bundle. A second run for one version forks the trend line.

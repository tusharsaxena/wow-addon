# Design — `/wow-addon:revendor-libka0s`

Date: 2026-08-24
Status: approved, pending implementation plan

## The problem

`LibKa0s` releases; its consumers do not follow. Today `../LibKa0s` sits at **v1.10.2** and
`../PanelMaster` bundles **v1.8.3** — two minors of drift, `LibKa0s-Media-1.0` absent entirely, and
both close-button fixes unreached. Nothing in the collection announces that. The vendored copy
still loads, every suite in the consumer stays green, and the only witness is somebody reading two
changelogs side by side.

Upstream documents the mechanics of catching up — `LibKa0s/docs/releasing.md` under
*Re-vendoring consumers* — but as a release-side checklist a human executes eight times. And the
harder half is not documented anywhere executable: once the bytes are current, **which of the new
surfaces should this addon actually adopt?** That question is answered today by re-reading
`docs/adoption-prompt.md` and re-deriving each addon's history from scratch.

This command is both halves, consumer-side, one repo at a time.

## What it is, and what it is not

It **re-vendors** the library's bytes into a target addon, **diffs** what changed since that
addon's copy, **recommends** which new surfaces are worth adopting, **interviews** the user per
candidate, **plans** the accepted ones, and **executes** them.

It is not a compliance audit (`standards-audit`), not a documentation sweep (`revendor-standards`,
`sync-docs`), and not a library-side fidelity report (`LibKa0s/docs/adoption-report.md`). It is the
only spec in this plugin besides `new-addon` that writes an addon's own Lua, and that boundary is
fenced explicitly rather than left to judgement.

## 1. Identity and shape

- File: `commands/revendor-libka0s.md`
- Invocation: `/wow-addon:revendor-libka0s`, also a Skill of the same name
- Acts directly; not a subagent wrapper

```yaml
argument-hint: [path | repo names | all]
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion]
```

Scope resolution mirrors `revendor-standards`: no arguments → the repo at cwd; names → those
siblings; `all` → every sibling directory holding a `libs/LibKa0s/`. Targets are processed
**sequentially, never fanned out** — each one costs the user a decision per candidate, and
concurrent interviews are not interviews.

## 2. Source of truth: the tag's tree, not the checkout

The library is read from the sibling checkout `../LibKa0s`, located relative to the target repo's
parent. If it is absent, the command **hard-stops**: it has nothing to copy, and a raw-GitHub
fallback would pull the `media/` binaries (icons, textures, fonts) over the wire for no gain.

The version copied is the **newest semver tag**:

```sh
git -C ../LibKa0s tag --sort=-v:refname | head -1
```

and the payload is extracted from that tag rather than from the working tree:

```sh
git -C ../LibKa0s archive <tag> LibKa0s testkit | tar -x -C <scratch>
```

This distinction is load-bearing. The consumer's `tests/test_vendor_sync.lua` reads the provenance
line, resolves the tag it names, and asserts both vendored payloads match the library **at that
tag**, file by file. A copy taken from a dirty checkout passes `diff -r` against the sibling and
then fails the consumer's own gate — the failure mode upstream already recorded for the untagged
kit revision.

The user may name an explicit tag; the command never silently takes `master`.

## 3. The delta — `01_DELTA.md`

Five reads, each recorded with the command that produced it. A claim without its command is not a
finding.

1. **Claimed version** — the provenance line in the target's `CLAUDE.md`, grepped as `[Bb]undles`
   so a mid-sentence phrasing is read correctly. The shape that satisfies it is *names the library
   and names the version*; a consistency sweep rewriting two true lines to match a template is
   wasted effort.
2. **Actual version** — the minor constants out of `libs/LibKa0s/*.lua`. The line is a claim; the
   minors are the fact. Disagreement between them is itself a finding, reported before anything is
   copied.
3. **Per-file minor delta** — old versus tag, every shipped file by its exact constant name:
   `MINOR` in `Core.lua`, `Media.lua`, `DebugLog.lua`, `Slash.lua`, `Options.lua` and `Perf.lua`;
   `WIDGETS_MINOR` in `OptionsWidgets.lua`; `SCROLL_MINOR` in `OptionsScroll.lua`; `PANEL_MINOR` in
   `PerfPanel.lua`. The file list is read from the tag's `LibKa0s.xml` rather than hard-coded, so a
   module added upstream appears without editing this spec.
4. **Both diffs, and the read of the difference** — `diff -r --strip-trailing-cr` (content, MUST be
   empty) and `diff -r` (bytes, SHOULD be empty), for `libs/LibKa0s/` and `tests/_kit/` alike.
   Content-clean with bytes-dirty means **nothing has forked**: the two checkouts disagree about
   line endings. The fix is renormalising the side that drifted
   (`git add --renormalize .`), **never** an edit to `libs/`.
5. **Consumption map** — `LibStub("LibKa0s-<Major>-1.0", true)` lookups outside `libs/` and
   `tests/`. A major present in the payload with no lookup anywhere is an unadopted module and
   feeds section 4.

Plus the **kit-revision delta** and its pairing rule: a consumer taking v1.9.0 or newer MUST take
kit revision 11 in the same commit, because the older `vendor_sync.lua` listed one directory level
and normalised line endings on everything — it reads `media` as a file and would mangle the
comparison of any binary containing the byte pair `0D 0A`.

## 4. The copy

Both payloads, **whole folders, always — never one module**. Per-module re-vendoring is precisely
how cross-major skew is manufactured: a new `Perf.lua` over an old `Core.lua`, or a `Core.lua` that
never arrived.

```sh
cp -r <scratch>/LibKa0s/.  <Addon>/libs/LibKa0s/
cp -r <scratch>/testkit/.  <Addon>/tests/_kit/
```

Then both diffs in both directions, then the provenance line in `CLAUDE.md` rolled to the resolved
tag.

**`cp -r` adds and overwrites; it does not delete.** A file removed upstream survives in the
consumer and the copy alone will never say so — the diffs are what catch it, as an `Only in
<Addon>/libs/LibKa0s` line. That is the one case where deleting inside `libs/` is correct, and it
is done only against that diff output, never on inference.

**Leftover README line.** If the target still carries the provenance line in `README.md`, this
command **removes it** while writing the correct line into `CLAUDE.md`, and announces the removal.
`sync-docs` nominally owns that migration, but leaving both produces the half-migrated
two-lines-that-can-disagree state upstream calls out, and this command is the one holding the
correct version at that moment. It removes only a line it has just superseded; it does not
otherwise touch the README.

**Gate before proceeding**: `luacheck .` and `lua tests/run.lua` — including
`tests/test_vendor_sync.lua` — must be green. Red stops the run with the output. A missing tool is
a **stated skip**, never an inferred pass.

**Commit**: one commit carrying both payloads *and* the provenance line. Upstream requires the
atomicity and the consumer's own gate fails a split.

## 5. Candidates — `02_CANDIDATES.md`

Derived from three sources, in order, never from memory and never from an API document's summary
paragraph:

- `git -C ../LibKa0s log --oneline <old-tag>..<new-tag>`
- the `CHANGELOG.md` version blocks in that range
- the `Since` markers in `LibKa0s/docs/api/<Major>/version-<minors>-docs.md` for every major whose
  minor moved — that directory is the source of truth for every public contract, versioned by
  folder precisely because different consumers run different versions at once

Every item lands in one of three classes, and only two are candidates:

- **Reached you on the re-vendor alone** — no host change required. Recorded as delivered, not
  offered. The v1.10.2 `PerfPanel` close-button fix is the worked example: `addonName` falls back
  to `name`, and every host in the collection already passes its folder name as `name`, so the fix
  arrives on the copy.
- **Host change required** — a new descriptor field, a new public surface, a new row type. A
  candidate.
- **Whole-module adoption** — a major this addon does not consume at all. A candidate, with a
  heavier blast radius, and carrying the addon's **own recorded reason for declining** if one
  exists (searched in its issue store and `docs/`), so a structural refusal like `BankLedger`'s
  no-combat-path decline of Perf is not re-litigated every release.

Each candidate carries a recommendation and its evidence as `file:line` into the API document or
the changelog.

## 6. The interview — `03_DECISIONS.md`

One candidate at a time, with its evidence in front of the user. Ordering: **fixes a live defect**
→ **closes a recorded gap** → **new capability**, ties broken by smallest blast radius first.

Three outcomes: **adopt**, **not now**, **never**.

- The command states **up front** that a decline becomes a **public** GitHub issue, rather than
  letting the user discover it from a notification.
- Decisions are written to `03_DECISIONS.md` as each one lands, not batched at the end, so an
  interrupted run leaves a record of what was actually decided.
- An early stop leaves the remaining candidates **undecided and untouched**. Silence is never
  adoption, and nothing the user never saw is implemented.

**Declines are filed.** A *not now* becomes a `state:triaged` GitHub issue with a severity; a
*never* becomes `state:will-not-do`. Both go through the `gh issue` subcommands the collection uses
— never `gh api graphql` — and both carry the rationale in the body, matching how
`adoption-prompt.md` cites per-addon issue IDs for declined Perf. `gh` is load-bearing for this
step: absent or unauthenticated, the command records the decision in the bundle and reports the
unfiled issue rather than degrading silently.

## 7. Plan and execute — `04_EXECUTION_PLAN.md`

Per adopted candidate the plan names: the files it touches, the **characterization test written
before** anything untested is modified, the assertion that actually proves the change, and the
commit boundary.

The assertion standard is upstream's: the library-versus-host question is *does this render the
same bytes*, not *does this still run*. The divergences that matter — colour codecs,
EditBox-versus-Dropdown dispatch, `hasAlpha`, an unknown `row.type` silently dropping a row from a
page — fail silently and only in-game, and none of them appear headless unless the assertion is
written.

Execution is one candidate at a time: test, then code, then `luacheck` + the headless harness
green, then **its own commit**.

Hard fences, stated in the command body:

- `libs/`, `Libs/` and `tests/_kit/` are **read-only**. A defect in either payload is an
  `[upstream]` finding — reported, that candidate stopped, fixed in the library repo and
  re-vendored. A local patch is reverted silently by the next copy and returns as a regression with
  no cause in the consumer's history.
- Setup files hold a **descriptor plus a degradation stub** and nothing else. The shared subsystems
  are consumed, not written. Anything genuinely missing goes upstream as an **additive** field, not
  worked around in the host.
- No behaviour change inside a mechanical diff; no body dumped into a nameless helper
  (anti-pattern #52).
- **Never pushes.** Push remains `finalize`'s job.

## 8. Summary — `05_SUMMARY.md` and chat

Tag moved from → to; the per-file minor table; what reached the addon for free; what was adopted
and its commit; what was declined, why, and its issue number; what was skipped and why; the suite
results at each gate.

The bundle lives at `docs/revendor/<YYYY-MM-DD>/` in the **target addon**, and is **frozen** —
`harvest-standards` reads it as evidence, and no spec edits a past bundle.

## 9. Boundaries

| Against | The line |
|---|---|
| `revendor-standards` | Same verb, different object. That one carries the standard's **reference** down and never copies its text (anti-pattern #49). This one carries the library's **bytes** down and writes code. |
| `new-addon` | First adoption at scaffold time; this is re-vendor and incremental adoption forever after. |
| `run-tests` | `run-tests` owns suites as a gate and offers to fix them. This runs them as its own stage gate and **stops** on unrelated red rather than fixing it mid-run. |
| `bump-version` | Must never roll the provenance `vX.Y.Z` — that is the library's tag, not the addon's. This command is the **only** one that moves it. |
| `LibKa0s/docs/adoption-report.md` | Read-only, library-side, every consumer at once. This is write-side, consumer-side, one repo at a time. |
| `harvest-standards` | Reads `docs/revendor/` bundles as evidence. Frozen — no spec edits a past bundle. |
| `sync-docs` | Owns migrating a provenance line out of a README as part of a doc sweep. This command removes only a README line it has just superseded, in the same commit as the bytes. |

## 10. Ripple in this repo

Five touches, not the usual four:

1. `commands/revendor-libka0s.md` — the new spec
2. `README.md` — a row in the **Commands** table
3. `.claude-plugin/plugin.json` — description, and the version → **2.1.0** (additive command)
4. `.claude-plugin/marketplace.json` — the mirrored description
5. `CLAUDE.md` — the *Artifact directories in the target addon* rule enumerates the dated trees and
   gains `docs/revendor/<date>/`; the *Vendored folders … are read-only* rule gains this command as
   the one that legitimately replaces them wholesale

LF line endings throughout, per this repo's `.gitattributes`.

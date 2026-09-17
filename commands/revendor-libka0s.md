---
description: Re-vendor LibKa0s into an addon from the library's newest tag, then decide what to do with what arrived. Copies both payloads whole (libs/LibKa0s/ and tests/_kit/), rolls the CLAUDE.md provenance line in the same commit, and reports the delta — per-file LibStub minors, both diffs, the kit-revision pairing rule, which majors this addon actually consumes, and contract changes under surfaces whose signature did not move, which are adoption blockers rather than candidates. Then works out which new surfaces are candidates for adoption, recommends per candidate with file:line evidence out of the library's own docs/api/, interviews you one at a time most-valuable-first, and implements what you accept — characterization test first, luacheck and the headless harness green, one commit per candidate. Declines are filed as GitHub issues. Writes a frozen bundle to docs/revendor/<date>/. Read-only on libs/ and tests/_kit/ apart from the copy itself; never pushes.
argument-hint: [path | repo names | all] [--tag vX.Y.Z]
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion]
---

Carry the current **LibKa0s** into the addon(s) in scope, and then decide what to do with what arrived. Scope comes from `$ARGUMENTS` (Step 1); with no arguments this is the repo at cwd.

## What this is, and what it is not

`LibKa0s` releases; its consumers do not follow. Nothing announces the gap: the vendored copy still loads, every suite in the consumer stays green, and the only witness is somebody reading two changelogs side by side. The library's own `docs/releasing.md` documents the catch-up under *Re-vendoring consumers*, but as a release-side checklist a human runs once per consumer — and the harder half is written down nowhere executable: once the bytes are current, **which of the new surfaces should this addon adopt?**

This command is both halves, consumer-side, one repo at a time. It re-vendors, diffs, recommends, interviews, plans, and implements.

**Keep it apart from its neighbours.** These lines are all places a run will otherwise blur:

| Against | The line |
|---|---|
| `/wow-addon:revendor-standards` | Same verb, different object. That one carries the standard's **reference** down and must never copy its text into a repo (anti-pattern #49). This one carries the library's **bytes** down, and writes code. |
| `/wow-addon:new-addon` | First adoption at scaffold time. This is re-vendor and incremental adoption forever after. |
| `/wow-addon:run-tests` | That command owns running suites as a gate and offers to fix what is red. This runs them as its own stage gates and **stops** on unrelated red rather than fixing it mid-run. |
| `/wow-addon:bump-version` | It must **never** roll the provenance `vX.Y.Z` — that is the library's tag, not the addon's. **This command is the only one that moves it.** |
| `/wow-addon:sync-docs` | It owns migrating a provenance line out of a README as part of a doc sweep. This command removes only a README line it has **just superseded**, in the same commit as the bytes. |
| `LibKa0s/docs/adoption-report.md` | Read-only, library-side, every consumer at once. This is write-side, consumer-side, one repo at a time. |
| `/wow-addon:harvest-standards` | It reads `docs/revendor/` bundles as evidence. They are **frozen** — never edit a past bundle. |

This is, with `new-addon`, one of only two specs in this plugin that writes an addon's own Lua. Step 7's fences are what make that safe; do not relax them.

## Step 1 — Resolve the scope

The `$ARGUMENTS` tokens, in any order:

- **`--tag vX.Y.Z`** → re-vendor that tag instead of the newest. Everything else is unchanged.
- **absent, or a path** → the repo at that path, defaulting to cwd. **This is the default.**
- **repo names** → those siblings, matched case-insensitively. No match → say so, list the candidates, stop.
- **`all`** → every sibling directory holding a `libs/LibKa0s/`:

  ```sh
  ls -d ../*/libs/LibKa0s 2>/dev/null
  ```

  The filesystem is authoritative here, not the library's Consumers table — that table is maintained by hand and the wiring is not. A repo with `libs/LibKa0s/` that the table does not name is worth reporting, but it is still in scope.

Targets are processed **sequentially, never fanned out.** Each one costs the user a decision per candidate, and concurrent interviews are not interviews. Announce the roster before starting and say which repo you are on at each transition.

A target that is not an addon repo — no `.toc`, or no `libs/LibKa0s/` — is **skipped with a reason**, not scaffolded. This command re-vendors an existing adoption; a first adoption is `new-addon`'s.

## Step 2 — Resolve the library, and take the payload from the tag

The library is the sibling checkout `../LibKa0s`, relative to the target's parent.

**Absent → hard stop.** There is nothing to copy, and there is no raw-GitHub fallback: the payload now includes `media/` (icon TGAs, statusbar textures, a font), and pulling binaries over `curl` to reconstruct a tree is a worse copy of a copy that is sitting on disk.

Resolve the version:

```sh
git -C ../LibKa0s tag --sort=-v:refname | head -1
```

Then extract **from that tag**, not from the working tree:

```sh
git -C ../LibKa0s archive <tag> LibKa0s testkit | tar -x -C <scratch>/
```

**This distinction is load-bearing and is not a stylistic preference.** The consumer's own `tests/test_vendor_sync.lua` reads the provenance line, resolves the tag it names, and asserts both vendored payloads match the library **at that tag**, file by file. A copy taken from a dirty checkout passes `diff -r` against the sibling and then fails the consumer's gate — which is exactly how the untagged kit revision was caught upstream. Re-vendor from a tag, and move the line in the same commit.

If `git archive` fails, or the working tree is dirty in a way that suggests the user meant the tree rather than the tag, **say so and ask**. Never silently take `master`.

## Step 3 — Establish the delta → `01_DELTA.md`

Six reads. **Each one is recorded with the command that produced it — a claim without its command is not a finding.**

### 3a. Claimed version

```sh
grep -n '[Bb]undles' <Addon>/CLAUDE.md
```

Grep case-insensitively and tolerate mid-sentence phrasing. What the template fixes is the **shape, not the wording**: a line that names the library and names the version satisfies it wherever it sits in a sentence. A capital-anchored sweep once reported a repo as carrying no provenance line at all when it had always had one. Do not rewrite two true lines to look alike.

### 3b. Actual version

```sh
grep -hoE 'local (MAJOR, )?(MINOR|WIDGETS_MINOR|SCROLL_MINOR|PANEL_MINOR) *= *("[^"]+", *)?[0-9]+' \
  <Addon>/libs/LibKa0s/*.lua
```

The line is a **claim**; the minors are the **fact**. Disagreement between them is itself a finding, reported before anything is copied — a line ahead of the bytes means somebody rolled the version without the payload, and a line behind means the reverse.

### 3c. Per-file minor delta

Old versus tag, every shipped file by its **exact constant name** — the secondary files carry their own name rather than `MINOR` because they attach to a shell that already owns that local:

| File | Constant |
|---|---|
| `Core.lua`, `Media.lua`, `DebugLog.lua`, `Slash.lua`, `Options.lua`, `Perf.lua` | `MINOR` |
| `OptionsWidgets.lua` | `WIDGETS_MINOR` |
| `OptionsScroll.lua` | `SCROLL_MINOR` |
| `PerfPanel.lua` | `PANEL_MINOR` |

**Read the file list from the tag's `LibKa0s/LibKa0s.xml`, not from that table.** The table is what the names look like today; the XML is what shipped. A module added upstream must appear in this delta without anyone editing this spec.

A consumer behind on any file is **cross-major skew**, and it is the most serious thing this step can find: it is the failure mode whole-folder vendoring exists to prevent, and it does not announce itself at runtime. Report the file, both minors, and what the consumer therefore does not have.

### 3d. Both diffs — and read the difference between them

For each payload, both directions:

```sh
diff -r --strip-trailing-cr <scratch>/LibKa0s <Addon>/libs/LibKa0s   # content — MUST be empty
diff -r                     <scratch>/LibKa0s <Addon>/libs/LibKa0s   # bytes  — SHOULD be empty
diff -r --strip-trailing-cr <scratch>/testkit <Addon>/tests/_kit
diff -r                     <scratch>/testkit <Addon>/tests/_kit
```

Three readings, and only one of them is a fork:

- **Content dirty** → a copy has genuinely forked. Re-vendoring is the fix.
- **Content clean, bytes dirty** → **nothing has forked.** The two checkouts merely disagree about line endings, which `git status` will never show you because the blobs are LF on both sides either way. The fix is to renormalise whichever side drifted (`git add --renormalize .`; if the working tree does not flip, delete the affected paths and `git checkout -- .` to pull them back through the filter). It is **never** an edit to `libs/` — editing the vendored copy to settle a line-ending disagreement creates a fork to fix a fork that was not there.
- **`Only in <Addon>/libs/LibKa0s`** → a file removed upstream that survives here. See Step 4.

### 3e. Consumption map

```sh
grep -rnoE 'LibStub\("LibKa0s-[A-Za-z]+-1\.0", true\)' <Addon> --include='*.lua' \
  | grep -v '/libs/' | grep -v '/tests/'
```

Every lookup site, with its file. A major present in the payload with **no lookup anywhere** is an unadopted module, and feeds Step 5. A second lookup site nobody recorded is worth naming on its own — that is how a consumer's schema file went unnamed in the library's Consumers table for a whole adoption cycle.

### 3f. Kit revision, and the pairing rule

```sh
grep -n 'Kit.VERSION' <scratch>/testkit/framework.lua <Addon>/tests/_kit/framework.lua
```

**A consumer taking LibKa0s v1.9.0 or newer MUST take kit revision 11 in the same commit.** Before revision 11, `vendor_sync.lua` listed one directory level and normalised line endings on everything — it reads `media` as a file, and would mangle the comparison of any binary containing the byte pair `0D 0A`. Since both payloads are copied whole in Step 4 this is satisfied by construction, but state it in the bundle: it is the reason the two payloads move together rather than independently.

### 3g. Contract delta — what moved without changing shape

Every read above compares a **number** or a **byte**, and there is one class of change neither can see: a surface that keeps its name, keeps its arguments, and changes what it does with them — *when* it is called, or what it now requires back from something the host supplied. That change arrives on the copy in Step 4, and then passes `luacheck`, passes the headless harness, and passes `tests/test_vendor_sync.lua`, which compares bytes and finds the bytes perfectly correct. It is wrong only on screen.

The worked example is the one this read was written for. `OptionsCompose.lua` minor 2 wrapped each of its three media rows as `values = function() return O.LSMValues(t) end`, so the host's member was reached at **dropdown-render** time and a member returning a *table* worked. Minor 3 drops that wrapper — `values = O.LSMValues(t)` — so the member is read **once, at row-declaration time**, and whatever it hands back is assigned straight into `values`. No signature moved on either side, and neither shape errors. `MultiMeters/settings/Schema.lua:670` supplies `C.LSMValues = function(mediaType) return lsmValues(mediaType)() end`, which returns a table: correct against minor 2, and under minor 3 it freezes that addon's font and texture dropdowns at whatever media happened to be registered when the schema file loaded. The library states the tightened half in the seam itself, at `OptionsCompose.lua:182`, and in its API document at `version-14.13.3.3-docs.md:50` and `:713` — including the one-line host fix, which is to pass the deferred reader rather than a caller of it.

**Which majors to read.** The ones 3c says moved a minor, intersected with the ones 3e says this addon actually looks up. A contract that changed under a module nobody consumes is not this addon's problem, and reading it anyway is how a delta report becomes long enough that nobody finishes it.

**Read both documents, not the new one.** `docs/api/<Major>/version-<minors>-docs.md` is written once per shipped version and never edited afterwards, so the old contract is still on disk exactly as the addon was built against it. Walk forward from the version the addon is on by each header's `Superseded by` row, which names the next document *and* glosses what moved in it, rather than guessing filenames. For `Options` and `Perf` the version key is a composite of every file's minor in load order — `14.13.2.3` is Options 14, Widgets 13, Compose 2, Scroll 3 — so the filename tells you that *something* moved and never which member:

```sh
git -C ../LibKa0s show <tag>:docs/api/<Major>/version-<new>-docs.md | head -20   # the header table
diff <(git -C ../LibKa0s show <old-tag>:docs/api/<Major>/version-<old>-docs.md) \
     <(git -C ../LibKa0s show <tag>:docs/api/<Major>/version-<new>-docs.md)
```

**Then read that diff for what is *not* new.** A `Since` marker is an addition; it belongs to Step 5, where the user decides. A changed sentence under a surface that already existed, or a MUST that appeared in this range, is a contract change and belongs here — the library documents its half of a seam by stating what the host owes it, and a new MUST is a MUST somebody's existing code was written before. In the worked example the document says so outright, in a section that did not exist a version earlier — "The one contract that tightened, for a host that supplies its own `LSMValues`" — and the `LSMValues` row itself gains a sentence while its surface, its `Since` marker and its arguments all stay put. That is the signature of this class: the tables look unchanged and the prose around them does not.

**Then bind it to what this addon actually hands over.** The `__Attach*` entry points are where a host passes members the library calls back, so they are where a moved call site can reach it:

```sh
grep -rn '__Attach[A-Za-z]*' <Addon> --include='*.lua' \
  --exclude-dir=libs --exclude-dir=Libs --exclude-dir=_kit
```

For each site, list the members the addon supplies and check every one against the new document's stated contract — the return shape, and when the library calls it. **A host-supplied member whose call site moved is the shape to look for**, and it is the whole class in a sentence.

**A contract change is an adoption blocker, not a candidate.** The distinction decides who is asked. A candidate is something this addon may decline and remain correct; a blocker is something it is *already* wrong about the moment the bytes land, so Step 6 never offers it and Step 5 never lists it. Record it in `01_DELTA.md` under its own **Blockers** heading with both documents' `file:line`, name it in `05_SUMMARY.md`, and fix the host in **Step 4's commit**, beside the payload and the provenance line — for the same reason those two already travel together, which is that there is no green-and-broken state worth leaving in the repo overnight.

If the fix needs a decision rather than an edit — the host's shape is deliberate, or the right replacement is not obvious from the document — **stop before the copy** and report the blocker with both versions quoted. Staying one release behind is recoverable and visible. Landing a payload that silently breaks a page, under a commit message saying every suite was green, is the outcome this read was written to prevent.

Write all of this to `docs/revendor/<YYYY-MM-DD>/01_DELTA.md` **before copying anything.** 3g is why that ordering is a rule rather than a habit: a blocker found after the copy is a blocker found in a repo that is already carrying it. If the delta is empty — same tag, both diffs clean, kit revision matching, nothing in 3g — say so, write the bundle, and stop. There is nothing to adopt from a release the addon already has.

## Step 4 — The copy

Both payloads, **whole folders, always. Never one module.**

```sh
cp -r <scratch>/LibKa0s/.  <Addon>/libs/LibKa0s/
cp -r <scratch>/testkit/.  <Addon>/tests/_kit/
```

Per-module re-vendoring is exactly how cross-major skew gets manufactured: an addon ends up carrying a new `Perf.lua` over an old `Core.lua`, or a `Core.lua` that never arrived at all. The only negotiation between majors is a **floor** — a dependent file names the minimum `NEEDS_CORE` it needs and returns before `NewLibrary` if the dependency is missing or older, so the module is **absent** rather than half-wired. That is the honest failure. Nothing negotiates the other direction.

**`cp -r` adds and overwrites; it does not delete.** A file removed upstream survives in the consumer, and the copy alone will never say so — the diffs are what catch it, as an `Only in <Addon>/libs/LibKa0s` line. That is the **one** case where deleting inside `libs/` is correct, and it is done only against that diff output, never on inference. Report every such deletion by name.

`tests/_kit/` is a sibling of the library's ship folder and never goes under `libs/` — `libs/` is the ship payload and the kit must never be zipped. Under `tests/` it is already covered by the `- tests` entry every addon's `.pkgmeta` carries, so this needs no packaging change.

Then re-run both diffs in both directions. **Content MUST now be empty.** If it is not, stop and report — do not proceed to adoption on a payload that did not land.

### The provenance line

Roll the line in `<Addon>/CLAUDE.md` to the resolved tag:

> Bundles [LibKa0s](https://github.com/tusharsaxena/LibKa0s) v*X.Y.Z* (MIT).

Preserve the repo's existing phrasing and position if it already has a line; only the version moves. `CLAUDE.md`, **never** `README.md` — the line answers "which LibKa0s does this build carry?", which is a maintainer's question on a page written for players, and the addon README carries no bundled-library inventory at all (`documentation-§1`, anti-patterns #58/#59). There is **no fallback**: `vendor_sync.lua` reads `CLAUDE.md`, and a line left in the README reads to it as no line at all.

**A leftover README line is removed here.** If the target still carries a provenance line in `README.md`, delete it while writing the correct one into `CLAUDE.md`, and **announce the removal**. `/wow-addon:sync-docs` nominally owns that migration, but leaving both produces the half-migrated two-lines-that-can-disagree state, and this command is the one holding the correct version at that moment. Remove **only** the line just superseded; touch nothing else in the README.

### Gate, then commit

```sh
cd <Addon> && luacheck . && lua tests/run.lua
```

Both green — including `tests/test_vendor_sync.lua`, which is the case this whole step exists to satisfy — before anything else happens. Red **stops the run** with the output shown; this command does not fix unrelated red (`run-tests` owns that). A missing tool is a **stated skip**, never an inferred pass and never a fabricated number.

Note that `luacheck`'s figure is scoped by `.luacheckrc`'s `exclude_files`, which in a consumer usually excludes `libs/` and `tests/`. A clean run only means something if the files carrying the seam are inside the checked set — confirm that before reading 0/0 as a clean adoption.

Then **one commit**, carrying both payloads *and* the provenance line together. The atomicity is required upstream and the consumer's own gate fails a split. Commit style per this collection: terse capitalized imperative subject, no Conventional-Commits prefix, `Co-Authored-By: Claude …` trailer.

**Never push.** Push is `/wow-addon:finalize`'s job, and `commit.md`'s hard rule stands.

## Step 5 — Work out the candidates → `02_CANDIDATES.md`

Three sources, in this order. **Never from memory, and never from an API document's summary paragraph.**

```sh
git -C ../LibKa0s log --oneline <old-tag>..<new-tag>
```

- the `CHANGELOG.md` version blocks in that range — each release block names every file's new minor and says what changed;
- the `Since` markers in `LibKa0s/docs/api/<Major>/version-<minors>-docs.md` for **every major whose minor moved**. That directory is the source of truth for every public contract, versioned by folder precisely because different consumers run different versions at the same time. Read the document for the **new** version and the one the addon was on, and diff the surfaces.

Every item lands in exactly one of three classes, and only two of them are candidates. **A contract change 3g already classed as a blocker is in none of them**: it was resolved in Step 4's commit or the run stopped before the copy, and re-offering it here would ask the user to approve something that is not optional.

**A. Reached you on the re-vendor alone.** No host change required. Recorded as *delivered*, not offered. The worked example is v1.10.2's `PerfPanel` close-button fix: `addonName` joins the descriptor as optional and falls back to `name`, and every host in the collection already passes its folder name as `name` — so the fix reaches an unmodified consumer on the copy. Getting this class wrong in the offering direction wastes the user's decision on work already done.

**B. Host change required.** A new descriptor field, a new public surface, a new row type, a new seam to call. **A candidate.**

**C. Whole-module adoption.** A major in the payload this addon does not consume at all (Step 3e). **A candidate**, with a heavier blast radius — and carrying the addon's **own recorded reason for declining**, if one exists. Search its issue store and its `docs/` before offering it:

```sh
gh issue list --search "LibKa0s" --state all --json number,title,state,labels
grep -rn 'LibKa0s' <Addon>/docs --include='*.md' | grep -iE 'declin|not adopt|no combat|exempt'
```

A structural refusal — the way `BankLedger` declines Perf because its capture engine never runs in combat and every bucket would read `0.000` by construction — is **settled**, not re-litigated every release. Report it as settled and move on unless the new version changes the premise, in which case say precisely which premise moved.

Each candidate carries:

- what it is, in one line;
- **evidence as `file:line`** into the API document or the changelog block;
- the files in this addon it would touch;
- a **recommendation** with its reasoning;
- its blast radius — additive, or does it replace code the addon currently owns and ships?

That last one matters more than it looks. A capability you **add** cannot regress: nothing was deleted, no existing test could break, the whole risk lives in code that did not exist yet. A module that **replaces** what the host owns means deleting real files and rewiring what survives onto a library seam through an adapter you write — and every deletion is a chance to change rendered output, lose a behaviour nobody wrote a test for, or silently drop a schema row. Say which kind each candidate is.

## Step 6 — Interview → `03_DECISIONS.md`

One candidate at a time, with its evidence in front of the user. **Order: fixes a live defect → closes a recorded gap → new capability**, ties broken by smallest blast radius first.

**Say up front, before the first question, that a decline is recorded as a public GitHub issue.** The user should hear that from this command, not discover it from a notification.

Three outcomes:

| Outcome | What it means | What is recorded |
|---|---|---|
| **adopt** | Implement it in this run | Goes to Step 7 |
| **not now** | Worth doing, not today | `state:triaged` issue with a severity |
| **never** | Structurally wrong for this addon | `state:will-not-do` issue with a severity |

Write each decision to `03_DECISIONS.md` **as it lands, not batched at the end**, so an interrupted run leaves a record of what was actually decided.

**An early stop leaves the remaining candidates undecided and untouched.** Silence is never adoption. Nothing the user never saw is implemented, and nothing un-shown is filed as a decline either — an unreached candidate is reported as unreached.

If the user cannot tell which of *not now* and *never* they mean, **ask again** rather than guess. A `will-not-do` on something they actually wanted loses real work; a `triaged` on something structurally impossible means re-declining it every release.

### Filing the declines

Through the `gh issue` subcommands the collection uses — `gh issue create`, `gh issue edit`, `gh label create --force`. **Never `gh api graphql`**, and never a hand-rolled GraphQL query; `gh api repos/{owner}/{repo}/issues` is the only acceptable REST fallback.

Every issue carries exactly **two labels that are the data**: one `state:` and one `severity:`. The title carries neither — no `[status]` prefix, no severity word. The body carries the rationale, the evidence `file:line`, and the library version the candidate came from, so a later run can tell a settled decline from a stale one.

`gh` is load-bearing for this step. Absent or unauthenticated, record the decision in the bundle and **report the unfiled issue** — do not degrade silently, and do not write a local ledger file instead (`docs/pending/LEDGER.md` is retired and no spec may recreate it).

## Step 7 — Plan and implement → `04_EXECUTION_PLAN.md`

Write the plan before touching code. Per adopted candidate it names: the files it touches, the **characterization test written before** anything untested is modified, the assertion that actually proves the change, and the commit boundary.

**The assertion standard is "does this render the same bytes", not "does this still run."** A test that passed before and after proves nothing if the code path moved. The divergences that matter here fail **silently and only in-game** — colour codecs, EditBox-versus-Dropdown dispatch, `hasAlpha`, an unknown `row.type` dropping one row from a page — and none of them appear headless unless the assertion is written. Write it.

Then implement, **one candidate at a time**: test, then code, then `luacheck` + `lua tests/run.lua` green (both through `~/.claude/wow-addon/bin/ka0s-bounded`), then **its own commit**. A candidate whose suites go red is rolled back to its own commit boundary and reported; it does not block the candidates after it.

Fences, all four of which hold on every candidate:

- **`libs/`, `Libs/` and `tests/_kit/` are read-only.** The copy in Step 4 is the only write this command makes to either, and it replaces them wholesale from the tag. A defect found in either payload is an **`[upstream]` finding**: report it, stop that candidate, fix it in the library repo, bump the file's LibStub minor, re-vendor the whole folder. A local patch is reverted silently by the next copy and the behaviour comes back as a regression with **no cause in the consumer's history**.
- **Setup files hold a descriptor plus a degradation stub, and nothing else.** The shared subsystems — chat printer, debug console, options toolkit, slash dispatcher, perf harness, test framework, media library — are **consumed, not written**. Anything genuinely missing goes upstream as an **additive** field, not worked around in the host. The rule of thumb that has held: one host's misfit is a setup-file concern; two is a library gap.
- **No behaviour change inside a mechanical diff**, no body dumped into a nameless helper (anti-pattern #52), no dispatch table built inside the function it serves.
- **Every close control goes through the one wrapper that supplies the addon's folder name.** A bare two-argument `Core.MakeCloseButton(frame, Hide)` is a defect on sight (`standalone-windows`, `debug-logging-§12`, anti-pattern #65) — it produces a perfectly good button, no layer errors, no suite goes red, and the only witness is somebody looking at two windows side by side. That defect has shipped twice upstream; do not let an adoption reintroduce it.

**Never push.**

## Step 8 — Summarise → `05_SUMMARY.md`, and report in chat

Both carry the same facts:

- the tag moved from → to, and the per-file minor table;
- what reached the addon **for free** (class A) — this is the part that is invisible otherwise;
- any **contract blocker** 3g found, both documents' lines, and how it was resolved — or that the run stopped before the copy because it was not;
- what was **adopted**, with each commit;
- what was **declined**, why, and its issue number;
- what was **skipped or unreached**, and why;
- the suite results at each gate, with any tool that was skipped named as skipped.

The bundle lives at `<Addon>/docs/revendor/<YYYY-MM-DD>/` and is **frozen**: a later run makes a new dated folder, and the difference between two folders is the record of what moved. `/wow-addon:harvest-standards` reads these as evidence — never edit a past bundle, and never rewrite one whose notation the standard has since retired. It records what was true against the library of *its* date, which is what a dated artifact is for.

In a multi-repo run, print a per-repo summary as each repo finishes rather than one at the end, and a final roster line saying which repos completed, which were skipped, and which the user stopped.

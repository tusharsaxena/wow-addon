---
description: Record and interpret an in-game perf run. Takes the report and the JSON dump the player copied out of the client after `/<slash> perf finish`, and writes a frozen bundle to docs/perf-analysis/<YYYYMMDD-HHMMSS>/ — report.md, dump.json and the ANALYSIS.md write-up. The report and the dump are mandatory inputs: if they are not in the prompt, ask for them and stop until they arrive. Fetches the living PERF_ANALYSIS.md playbook from the standards repo. Never invents a capture.
argument-hint: [paste the copied perf log — the report and the JSON dump — or omit and be asked]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, WebFetch, AskUserQuestion]
---

Record an **in-game** perf run for the addon at the cwd, and write the analysis of it.

This command is the in-game counterpart to `/wow-addon:automated-tests`. That one *runs* four
out-of-game suites and records them; this one cannot run anything — the measurement happened in a
live client, on the player's machine, in combat, and it exists only as text the player copied out of
the game. **This command's entire job is to turn that paste into evidence and read it.** Offline perf
scenarios are not this command's business; they live in the automated-test bundle that produced them
(`automated-tests-§7`).

## Step 0 — Fetch the playbook

The process spec is **living** and lives in the standards repo. Fetch it rather than working from
memory:

- **`PERF_ANALYSIS.md`** — <https://raw.githubusercontent.com/tusharsaxena/WowAddonStandards/master/PERF_ANALYSIS.md>

Also fetch the standard's entry point and follow its Sections list to the **`performance`** section,
which is where the normative rules live (the capture protocol, the record schema, the bundle, and
what an analysis owes its reader):

- **`standards/STANDARDS.md`** — <https://raw.githubusercontent.com/tusharsaxena/WowAddonStandards/master/standards/STANDARDS.md>

Hard-code only that entry point and discover the section file by **following the Sections list** —
never hard-code an individual section filename.

Follow the playbook to the letter. Everything below is orchestration; the playbook is the spec.

## Step 1 — Confirm the addon has the harness

An addon that cannot produce a capture cannot have one recorded for it. Check, in the repo at the
cwd:

- **`core/PerfSetup.lua`** — the descriptor that hands the addon's buckets, suspend/resume contract
  and SV name to `LibKa0s-Perf-1.0` (`performance-§1`, `performance-§3`).
- **`docs/perf-analysis/`** — the standing capture store, with its `README.md` (`performance-§8`).
- A second SavedVariables global `<Addon>PerfDB` in the TOC (`performance-§5`).

If the descriptor is **missing**, the addon has not wired the harness. Say so, name what adoption
needs, and **stop** — do not offer to synthesize a run.

**Decide this by looking, never from a remembered roster.** `core/PerfSetup.lua` is the test: an
addon that has it supports a capture, and an addon that does not, does not. A list of supporting
addons written into this file goes stale the first time a fourth addon wires the harness, and the
roster of in-scope addons has one home (`standards/ADDONS.md`) which is not here. Distinguish the two
ways the descriptor can be absent, because they need opposite answers: an addon that simply has not
adopted the harness **should**, and an addon carrying a recorded **no-combat-path exemption**
(`performance-§12`) never will — it ships no `docs/perf-analysis/` at all, and naming the exemption
is the correct answer there rather than creating the directory. `docs/performance.md` is where an
addon records which of the two it is.

If the descriptor is present but `docs/perf-analysis/` is not, create the directory and its
`README.md` as part of this run and say that you did — a first capture is exactly when that store
comes into existence.

## Step 2 — Get the report and the dump. This is mandatory.

**Both inputs come from the player. You cannot produce either one, and you MUST NOT proceed without
them.** The client is on the user's machine; there is no path from this session into it.

If `$ARGUMENTS` already carries the paste, use it. Otherwise **ask, and stop** — do not explore the
repo, do not draft an analysis skeleton, do not guess a plausible capture from a previous run. Ask
for exactly this, naming the verbs that produce it:

> Paste the perf run's output. In the client, after the run:
>
> 1. `/<slash> perf report` — the summary
> 2. `/<slash> perf dump` — one line of JSON
>
> then hit **Copy** on the debug-log window (`Ctrl+C`, `Esc`) and paste the whole buffer here. One
> paste is fine — the report and the dump come out of the same window and I will split them.
>
> If you would rather read it off disk, the record is also in
> `_retail_/WTF/Account/<ACCOUNT>/SavedVariables/<Addon>.lua` under `<Addon>PerfDB.runs` after a
> `/reload`; paste the run you want recorded.

Substitute the addon's real slash verb (`/at` for AbsorbTracker, `/kcd` for KickCD, `/cm` for
ConsumableMaster — read it from the addon's slash registration rather than assuming).

**A run with a report and no dump, or a dump and no report, is not a bundle.** Ask for the missing
half. The report is what a human reads; the dump is the machine-checkable record the report's
figures must reconcile against, and an analysis with only one of them cannot be verified by the next
reader (`performance-§8`).

## Step 3 — Split, validate, and derive the stamp

The paste is one debug-log buffer. Every line is `HH:MM:SS | [Tag] <text>`. Split it by tag and
content, do not ask the user to do it:

- **The report** — the `[Perf]` block that starts at `capture: <label>  (<Addon>, schema N, vX.Y.Z)`
  and runs through the `who:` / `where:` / `group:` context lines, the `active:` / `suspended:` /
  `delta:` arms, the bucket table, and the trailing `(buckets nest: … — do not sum)` note.
- **The dump** — the single `[Perf]`-tagged line whose text is one JSON object beginning `{"addon":`.
- **Everything else** — the run's lifecycle lines (`run started`, `experiment A armed`,
  `Experiment A RECORDING`, `ENDED`, `run finished`, `addon SUSPENDED`/`RESUMED`), plus any
  `[Combat]`, `[Bar]`, `[Init]`, `[World]` lines. **Keep these.** They are the provenance of the
  capture — they are how a later reader can tell that arm B really was suspended, that both arms
  really were combat-gated, and that a `/reload` did not land between them. They go into `report.md`
  under their own heading.

Then validate, and **say what you checked**:

| Check | Why it matters |
|---|---|
| `dump.addon` equals the addon at the cwd | A capture filed under the wrong repo is worse than an unfiled one |
| `dump.version` matches the TOC's `## Version` | A capture is only comparable against runs of a known build |
| `dump.schema` matches the vendored lib's `lib.SCHEMA` | A record under a superseded schema is not the shape the next reader will parse |
| The report's figures appear in the dump | The report is `%.1f`/`%.2f`-rounded; the dump carries `%.4f`. They must **reconcile**, not match to the digit |
| Both arms have `frames > 0` | `deltaMsPerFrame` is hard-coded `0` unless both ran — a `0.00` delta from a one-armed run is not a null result, it is an absent one |

A mismatch is **reported, not corrected**. If `dump.addon` is another addon, stop and say so. If the
version disagrees with the TOC, record the capture and state the discrepancy in the analysis — the
record is what the client emitted and it stands.

**Derive the bundle stamp from the capture, not from now.** Convert `dump.timestamp` (epoch seconds)
to **local time** as `YYYYMMDD-HHMMSS`:

```sh
date -d "@<timestamp>" +%Y%m%d-%H%M%S      # e.g. 1786087202 -> 20260807-125002
```

The folder names when the run happened. A capture pasted a week later still sorts against its
neighbours, which is the whole reason the store is cumulative. Local time, with the same rationale
`automated-tests-§1` gives for its bundles — the person reading it thinks in the clock they ran it
on. If `dump.timestamp` is `0` or absent, fall back to the `label`'s `YYYY-MM-DD HH:MM` stamp with
`00` seconds, and **say in the analysis that the stamp was reconstructed**.

## Step 4 — Write the bundle

Create `docs/perf-analysis/<YYYYMMDD-HHMMSS>/` and write exactly three files:

```
docs/perf-analysis/
  README.md                     -- what this store is and how a capture is taken (standing)
  <YYYYMMDD-HHMMSS>/
    report.md                   -- the human-readable report, as the client printed it
    dump.json                   -- the record, verbatim, one line
    ANALYSIS.md                 -- the write-up (Step 5)
```

- **`report.md`** — the copied output, in fenced blocks, under the playbook's headings. Keep the
  `HH:MM:SS | [Tag] ` prefixes: they are timestamps, and the gap between `Experiment A ENDED` and
  `Experiment B RECORDING` is a fact about the capture.
- **`dump.json`** — the JSON line **exactly as the client emitted it**, byte for byte. Do not
  pretty-print it, do not re-order its keys, do not round a figure, do not strip a field you think is
  wrong. The library already emits sorted keys so two records diff cleanly, and the encoder's own
  quirks (`%.4f` on every non-integer, an empty table encoding as `{}` rather than `[]`) are part of
  the record's identity. A reformatted record no longer diffs against its neighbours, and a
  hand-touched one is worse than an absent one because it reads as measured. Use `jq` to *read* it;
  never to rewrite it into the file.

## Step 5 — Write `<bundle>/ANALYSIS.md`

Use the playbook's template **verbatim in structure**. The rules under most pressure, restated:

- **Never fabricate a number.** Every figure comes from `report.md` or `dump.json` in this bundle.
  Cite the file, and link it from the row — a reader should reach the evidence in one click.
- **The buckets are the addon's cost. The frame-time delta usually is not.** `deltaMsPerFrame` is a
  difference of two noisy aggregates, with a resolution floor around **±0.3 ms/frame** on a 60–80 s
  arm. Below roughly **0.5 ms/frame** it is **unresolved**, which is not the same fact as zero, and
  saying "no measurable impact" when the instrument could not have measured one is the single most
  common way one of these write-ups goes wrong. Read the buckets, which measure the addon's own code
  directly.
- **A negative sign is not a result.** The suspended arm reading *slower* than the active arm means
  the environment moved between the arms — it is the tell, and it is worth stating as one.
- **Say what the arms did not hold constant.** Different zones, unequal durations, a group that
  changed size, another player wandering past. The report's `who:` / `where:` / `group:` block and
  the lifecycle lines are the evidence; a capture whose arms differ in environment measures the
  environment.
- **Declared nesting is not observed nesting.** A bucket whose row reads `declares itself within X —
  not observed` has an **unverified** parent claim, because no call site passed the parent. Say so.
  Do not silently present the declared tree as measured containment, and do not sum nested buckets —
  the report's own footer says not to.
- **A bucket absent from the table never fired.** That is a result about what the run exercised, and
  it belongs in the write-up rather than being passed over in silence.

Diff against the **previous** capture — the bundle directory sorting immediately before this one —
and say what moved. Compare `ms/s` and calls-per-pass ratios rather than raw totals: two runs of
different combat duration are not comparable on `totalMs`. If this is the first capture, say so and
treat every figure as a baseline rather than describing it as unchanged.

## Step 6 — Refresh `docs/perf-analysis/README.md`

The bundles are frozen; the store's `README.md` is the one file that is rewritten. It carries what is
**currently** true: the naming, a short schema summary, a pointer to the library's canonical
field-by-field contract, the fact that offline runs live in `docs/automated-tests/`
(`automated-tests-§7`), and a **table of the captures taken so far** — stamp, addon version, label,
one line on what it measured, and a link. That table is the store's index; a reader looking for "the
last capture on 1.9.0" should not have to open six directories.

## Step 7 — Report

Print:

- The bundle path, the derived stamp, and where the stamp came from.
- The headline in one line: the two arms, the delta, and whether the delta is **resolved**.
- The bucket table's top rows by `ms/s`, and the addon's total accounted cost per second of combat.
- What moved against the previous capture, or that this is the first.
- Every validation from Step 3 that did **not** pass, stated plainly.
- A reminder that the bundle and the README are uncommitted changes for the user to review.

## Hard rules

- **Never invent, complete, or reconstruct a capture.** No report and no dump means no bundle. If the
  paste is truncated mid-table, ask for the rest — a bundle assembled from a partial paste plus
  inference is a fabricated measurement wearing the format of a real one, and nothing downstream can
  tell the difference.
- **Never edit a frozen bundle.** A bundle is evidence. If a reading was wrong, the *next* capture's
  analysis says so; this one stands as what was believed at the time (`audit-review-history`).
- **Never hand-write a number into a bundle**, and never "tidy" `dump.json`. Everything in it came
  out of the client.
- **Never read a delta below the resolution floor as a result**, in either direction. "Unresolved" is
  the honest word and it is a finding in its own right.
- **Never run the addon's test suites to fill a gap here.** The offline scenarios answer a different
  question and belong to `/wow-addon:automated-tests`; citing an offline `bytes/iter` as though it
  were in-game evidence conflates two harnesses the standard deliberately separates.
- **Don't commit.** This command records; committing is the user's call (`/wow-addon:commit`).
- **Never create `docs/perf-analysis/` in an addon with a recorded `performance-§12` exemption.** Say
  the addon is exempt and why. An empty store in an addon with no combat path is a directory that
  will never fill, and it reads as an unmet obligation forever.

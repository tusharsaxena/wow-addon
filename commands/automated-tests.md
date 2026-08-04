---
description: Run the addon's full automated-test battery through the vendored runner and record it — lint, headless tests, offline perf scenarios and lizard complexity — writing a frozen bundle to docs/automated-tests/<YYYYMMDD-HHMMSS>/, rolling the run into RESULTS.md, and writing the ANALYSIS.md write-up. Fetches the living AUTOMATED_TESTS.md playbook from the standards repo.
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, WebFetch]
---

Run and **record** the addon at the cwd's automated tests.

This is the recorded, four-suite run. For the fast green gate — lint and tests only, writing nothing
— use `/wow-addon:run-tests`, or the runner's own `--suite lint --suite tests --no-bundle`.

## Step 0 — Fetch the playbook

The process spec is **living** and lives in the standards repo. Fetch it rather than working from
memory:

- **`AUTOMATED_TESTS.md`** — <https://raw.githubusercontent.com/tusharsaxena/WowAddonStandards/master/AUTOMATED_TESTS.md>

Also fetch the standard's entry point and follow its Sections list to the **`automated-tests`**
section, which is where the normative rules live (what a bundle contains, what gates, what
`RESULTS.md` is):

- **`standards/STANDARDS.md`** — <https://raw.githubusercontent.com/tusharsaxena/WowAddonStandards/master/standards/STANDARDS.md>

Hard-code only that entry point and discover the section file by **following the Sections list** —
never hard-code an individual section filename.

Follow the playbook to the letter. Everything below is orchestration; the playbook is the spec.

## Step 1 — Confirm the addon has adopted the section

The runner is **vendored**: `tests/_kit/run-automated-tests.sh`, from `LibKa0s`'s `testkit/`.

- If it is **missing**, the addon has not adopted `automated-tests` yet. Say so, name what adoption
  needs (re-vendor `tests/_kit/` from the LibKa0s release the README's provenance line names, add
  `*.sh text eol=lf` to `.gitattributes`, create `docs/automated-tests/`), and stop.
- **Do not** hand-roll a substitute, and **do not** run the four tools individually and assemble a
  bundle yourself. A bundle whose provenance is "an agent ran some commands" is not the artifact the
  standard defines, and it will not compare against one that is.
- If it is present but **not executable**, `chmod +x` it and say so — `cp` does not reliably carry
  the bit across filesystems, so this is a normal re-vendor artifact rather than a finding.

## Step 2 — Run

From the repo root:

```sh
tests/_kit/run-automated-tests.sh                    # the default: all four, writes a bundle
tests/_kit/run-automated-tests.sh --label <text>     # when the run answers a specific question
tests/_kit/run-automated-tests.sh --suite <name>     # repeatable, for a subset
```

The runner writes the bundle and prepends the `RESULTS.md` row. It does **not** write `ANALYSIS.md`
or the `RESULTS.md` watch list — those need a reader, and they are Steps 3 and 4.

If the user asked for a subset, pass `--suite` and say in the report which suites were **not** run.
A partial run that reads as a full one is the same failure as a skipped suite reported as a pass.

## Step 3 — Write `<bundle>/ANALYSIS.md`

Use the playbook's template **verbatim in structure**. Two rules from it are worth restating because
they are the ones under pressure:

- **Never fabricate a number.** Every figure comes from `manifest.json` or a suite artifact in this
  bundle. Cite the file.
- **Never soften a skip into a pass.** "luacheck unavailable" is not "lint clean". If a suite was
  skipped, the analysis says what was not measured and why.

Diff against the **previous** run — the row above this one in `RESULTS.md` — and say what moved. If
this is the first run, say so and treat every figure as a baseline rather than describing it as
unchanged.

## Step 4 — Refresh the `RESULTS.md` watch list

Below the table, describe the **current** state: every function `lizard` warned on and every file in
`layout-§1`'s 1000–1500 on-notice band, each with a one-line disposition — *accepted and why*, *peel
next*, or *already tracked as `<deviation-id>`*. Mark anything that **newly** crossed since the
previous run.

Carry forward a disposition that is still true rather than re-arguing it. `None.` if the list is
empty — an empty watch list is a **result**, not a reason to drop the heading.

## Step 5 — Report

Print:

- One line per suite: name — status — headline figure. Tag `perf` and `complexity`
  **`(recorded, non-gating)`** so nobody reads a complexity count as a gate.
- The verdict (`green` / `amber` / `red`) and the bundle path.
- Anything that newly crossed a threshold, with its disposition.
- Every **skipped** suite, with what is missing and its install hint (`pipx install luacheck`,
  `pipx install lizard`, a Lua 5.1 interpreter). Never let a skip pass silently — recording skips is
  the whole reason a green run can be trusted.
- A reminder that the bundle and `RESULTS.md` are uncommitted changes for the user to review.

## Hard rules

- **Don't commit.** This command records; committing is the user's call (`/wow-addon:commit`).
- **Never edit a frozen bundle.** A bundle is evidence. If a reading was wrong, the *next* run's
  analysis says so; this one stands as what was believed at the time.
- **Never edit `tests/_kit/`.** It is vendored. A runner problem is fixed in `LibKa0s` and
  re-vendored; a local patch is reverted silently by the next re-vendor, and the behavior it fixed
  returns as a regression with no cause anywhere in this repo's history.
- **Never turn perf or complexity into a gate**, and never present them as one. They are measured and
  recorded. A complexity warning count is not a failure.
- **Never hand-write a number into a bundle.** Everything in it came from a tool. A hand-edited
  record is worse than an absent one, because it reads as measured.
- **A missing tool is a skip, not a failure** — report it as skipped with an install hint, never as a
  red suite.

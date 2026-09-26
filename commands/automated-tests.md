---
description: Run the addon's full automated-test battery through the vendored runner and record it — lint, headless tests, offline perf scenarios and lizard complexity — writing a frozen bundle to docs/automated-tests/<YYYYMMDD-HHMMSS>/, rolling the run into RESULTS.md, and writing the ANALYSIS.md write-up. Fetches the living AUTOMATED_TESTS.md playbook from the standards repo.
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, WebFetch]
---

Run and **record** the addon at the cwd's automated tests.

This is the recorded, four-suite run. For the fast green gate — lint and tests only, writing nothing
— use `/wow-addon:run-tests`, or the runner's own `--suite lint --suite tests --no-bundle`.

Everything here runs **outside** the game client. An **in-game** capture — the report and the JSON
dump a player copied out of the client after a `/<slash> perf` run — is `/wow-addon:perf-analysis`'s,
and lands under `docs/perf-analysis/<YYYYMMDD-HHMMSS>/`. The offline perf scenarios recorded below
answer a different question and are never a stand-in for one.

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
  needs (re-vendor `tests/_kit/` from the LibKa0s release the **root `CLAUDE.md`** provenance line
  names, add create `docs/automated-tests/`, and get `.gitattributes` right), and stop. On the
  provenance line: it lives in `CLAUDE.md`, **not** `README.md`, since LibKa0s v1.8.1 / test-kit
  revision 9, and the consumer-side gate has **no fallback** — a repo whose line is still in the
  README reads as having none at all, so the line must move into `CLAUDE.md` in the **same** commit
  as the re-vendored bytes, and `docs/test-cases.md` regenerates with it (the first case's name
  changed). On that last item, name
  the **whole** rule and not just the carve-out: if the repo has no `.gitattributes`, or has one with
  no `* text=auto eol=…` pin, the fix is to write the canonical body for the repo's kind — pin,
  `*.sh text eol=lf`, binary markings — and then renormalize (`line-endings`). Telling the user to
  "add `*.sh text eol=lf`" to a file that does not exist or states no rule produces exactly the
  carve-out-without-a-pin state the standard names as a defect in its own right.
- **Do not** hand-roll a substitute, and **do not** run the four tools individually and assemble a
  bundle yourself. A bundle whose provenance is "an agent ran some commands" is not the artifact the
  standard defines, and it will not compare against one that is.
- If it is present, test the **recorded index mode**, never the working-tree bit:
  `git ls-files -s tests/_kit/run-automated-tests.sh`. If it does not report **`100755`**, fix it and
  say so — this is a normal re-vendor artifact rather than a finding:

  ```sh
  chmod +x tests/_kit/run-automated-tests.sh
  git update-index --chmod=+x tests/_kit/run-automated-tests.sh
  git ls-files -s tests/_kit/run-automated-tests.sh   # re-check: expect 100755
  ```

  Do **not** decide this from `ls -l` or a `-x` test. `cp` does not reliably carry the bit; every repo
  here sits on a WSL **DrvFs** mount that reports every file as `rwxrwxrwx`, so the working tree always
  claims the file is executable; and every repo has **`core.fileMode=false`**, so git ignores the
  working tree's mode even when `chmod` does change it. The mode that survives a clone is the one git
  recorded, which is why `chmod +x` on its own leaves the file `100644` forever (`automated-tests-§2`).

## Step 2 — Run

From the repo root:

```sh
~/.claude/wow-addon/bin/ka0s-bounded tests/_kit/run-automated-tests.sh                    # the default: all four, writes a bundle
~/.claude/wow-addon/bin/ka0s-bounded tests/_kit/run-automated-tests.sh --label <text>     # when the run answers a specific question
~/.claude/wow-addon/bin/ka0s-bounded tests/_kit/run-automated-tests.sh --suite <name>     # repeatable, for a subset
```

**Every run goes through the bounded runner.** Prefix each command with `~/.claude/wow-addon/bin/ka0s-bounded` (e.g. `~/.claude/wow-addon/bin/ka0s-bounded lua tests/run.lua`). It caps process memory, process-tree memory and wall-clock time, and queues on a machine-wide slot pool, so running several repos' suites **in parallel** is fine — the pool, not you, decides how many run at once. The plugin's `PreToolUse` hook refuses an unbounded `lua tests/run.lua` / `tests/perf.lua`, `run-automated-tests.sh`, `luacheck` or `lizard` (a repo whose `tests/_kit` is kit revision 23+ self-bounds its Lua runs and is let through). A run that exits **124** hit the time limit and **137** was killed, most likely by the memory limit — report either as exactly that, never as a test failure or a pass.

The runner writes the bundle and prepends the `RESULTS.md` row. It does **not** write `ANALYSIS.md`
or the `RESULTS.md` watch list — those need a reader, and they are Steps 3 and 4.

**Capture the run's console output to a path no other run can share.** Several repos' batteries often
run at once (parallel subagents, or one session sweeping the collection), and a fixed name such as
`/tmp/run.log` or `run.log` in a shared directory lets one run overwrite another's log mid-read, so the
analysis cites the wrong repo's figures. Put the repo name and a unique suffix in the path, in your
scratchpad directory when you have one, and never inside the repo (the log is not part of the bundle):

```sh
log=$(mktemp "${TMPDIR:-/tmp}/ka0s-ats-$(basename "$PWD")-XXXXXX.log")
~/.claude/wow-addon/bin/ka0s-bounded tests/_kit/run-automated-tests.sh >"$log" 2>&1; echo "exit $?"
```

Read the bundle path and the verdict from that log, and cite figures from the bundle's own files, not
from the log.

If the user asked for a subset, pass `--suite` and say in the report which suites were **not** run.
A partial run that reads as a full one is the same failure as a skipped suite reported as a pass.

## Step 3 — Write `<bundle>/ANALYSIS.md`

Use the playbook's template **verbatim in structure**. Two rules from it are worth restating because
they are the ones under pressure:

- **Never fabricate a number.** Every figure comes from `manifest.json` or a suite artifact in this
  bundle. Cite the file, and **link it from the row** — a reader should reach the evidence in one click.
- **Report complexity in full — totals *and* averages.** `manifest.json`'s `suites.complexity` carries
  every field of `lizard`'s footer. A total that rose because the addon grew is a different fact from
  an average that rose because it got denser, and only the second is a complexity signal.
- **Never soften a skip into a pass.** "luacheck unavailable" is not "lint clean". If a suite was
  skipped, the analysis says what was not measured and why.

Diff against the **previous** run — the row above this one in `RESULTS.md` — and say what moved. If
this is the first run, say so and treat every figure as a baseline rather than describing it as
unchanged.

**When this runs as a subagent, the Write tool may refuse `ANALYSIS.md`** (a guard that stops
subagents writing report files). That refusal is not a reason to skip the file: `ANALYSIS.md` is part
of the bundle the standard defines. Write the text to a file in your scratchpad directory (with the
Write tool there, or `cat > "$scratch/ANALYSIS.md" <<'EOF'`), then `cp` it to
`<bundle>/ANALYSIS.md`. The bounded-runs hook reads only command position, so a heredoc body that
names `lizard` or `luacheck` passes; never set `KA0S_BOUNDED_HOOK=off` to get a write through. The
same route applies to any other file in this command that Write refuses.

## Step 4 — Refresh the `RESULTS.md` standing sections

Below the table, describe the **current** state — four sections, one per suite (the playbook gives
each in full):

- **`## Test suite`** — case count and coverage; flag a count that has not moved while the addon has.
- **`## Lint`** — clean or not, over how many files, and **what `.luacheckrc` excludes**. A `0/0` row
  means nothing without knowing what was in scope.
- **`## Perf`** — the scenarios and what they pin, or a plain statement that the addon ships none and
  that the run is therefore silent about runtime cost.
- **`## Complexity watch list`** — **two tables, both with header rows** (a bare row of pipes renders
  as literal pipes, not a table): warned functions as Function / CCN / Location / Disposition, and
  files as **Band** / File / LOC / Disposition with the band as a *column* so more than today's two
  bands render uniformly. Anything that **newly** crossed is marked as such.

A disposition has a **shelf life**. An entry carried as **Accepted** across three consecutive
release runs is owed either a fix or a tracked deviation ID with an owner — check the previous rows
in `RESULTS.md`'s git history before writing "accepted" again, and say so in the run summary when one
crosses that line (`automated-tests-§4`, anti-pattern #53). A watch list where everything is accepted
costs maintenance and carries no signal.

When writing dispositions, remember `lizard` counts every `and`/`or` short-circuit as a decision: in
Lua a run of `t.k = rec.k or D.k` defaulting lines scores high with no visible branching, so say
whether a warned function is dense **defaulting/guarding** or genuinely tangled control flow. The two
want different fixes and carry different risk.

Do not let the complexity watch list be the only prose. It came first, and a record whose only
narrative is about complexity teaches the reader that the other three suites are pass/fail lights.

Carry forward a disposition that is still true rather than re-arguing it. `None.` where a section has
nothing to report — that is a **result**, not a reason to drop the heading.

## Step 5 — Report

Print:

- One line per suite: name — status — headline figure. Tag `perf` and `complexity`
  **`(recorded, non-gating)`** so nobody reads a complexity count as a gate.
- The verdict (`green` / `amber` / `red`) and the bundle path.
- Anything that newly crossed a threshold, with its disposition.
- Every **skipped** suite, with what is missing and its install hint (`sudo luarocks install luacheck`,
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
- **Never make this command gate on perf or complexity**, and never present a run as failed because of
  them. They are measured and recorded; a complexity warning count does not fail a run. The **release**
  gate — all four suites plus zero functions above CCN 15 — belongs to `/wow-addon:bump-version`, which
  reads this run's `manifest.json` before it edits anything. Do not implement it here, and never edit
  the vendored runner's exit code to implement it: the same script is the commit gate.
- **Never hand-write a number into a bundle.** Everything in it came from a tool. A hand-edited
  record is worse than an absent one, because it reads as measured.
- **A missing tool is a skip, not a failure** — report it as skipped with an install hint, never as a
  red suite.

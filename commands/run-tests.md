---
description: Run the current addon's entire test battery — auto-detects and runs luacheck lint, the headless Lua tests/ harness, and any Makefile `test` target, then reports a combined pass/fail summary. Offers to diagnose and fix failures.
allowed-tools: [Bash, Read, Glob, Grep, Edit]
---

Run the full test battery for the addon at the cwd and report the results.

## Step 0 — Locate the addon

Confirm the cwd looks like a WoW addon — at least one `.toc` file at the root (or a folder that is clearly an addon). If nothing testable is present at all, say so and stop; don't invent a harness.

## Step 1 — Discover and run suites

Discover what's present and run each applicable suite **in this order**, capturing output. Report every suite as **pass**, **fail**, or **skipped (tooling absent)** — a missing tool is a skip, not a failure.

1. **luacheck (static lint)** — if a `.luacheckrc` exists **and** `luacheck` is on `PATH`, run `luacheck .`. If `.luacheckrc` exists but `luacheck` is missing, mark it **skipped** and note the install hint. No `.luacheckrc` → not part of this addon's battery; skip silently.
2. **tests/ harness (headless Lua unit tests)** — the Ka0s standard's headless Lua 5.1 harness, built on the vendored shared test kit. Discover the runner (in order of preference): an explicit entry like `tests/run.lua` / `tests/run_tests.lua`, else suite files under `tests/` (`test_*.lua`, `*_test.lua`, `*_spec.lua`). Pick an interpreter, preferring `lua5.1` → `lua` → `luajit`. Run the harness **from the repo root** — the runner and the kit both assume it — and capture its pass/fail counts. If a `tests/` dir exists but no interpreter is found, mark **skipped** with the reason.

   **`tests/_kit/` is not a suite directory.** It is the vendored shared harness (`framework.lua`, `loader.lua`, `mock_base.lua`, `README.md`) — the runner `dofile`s it. Never glob it for suites, never run its files directly, never count anything in it, and never edit it (see the hard rules). Prefer the explicit runner precisely so this doesn't arise; if you fall back to globbing, exclude `tests/_kit/`.
3. **Makefile `test` target** — if a root `Makefile` defines a `test:` target, it is often the canonical entry point that already wraps lint + unit tests. **De-dup:** if `make test` clearly runs the same suites as 1–2, run `make test` **instead of** re-running those suites, and say so in the summary. If it does something additional (e.g. integration tests), run it as its own suite.

**Not a suite: measurement runners.** `tests/perf.lua` — the Ka0s standard's offline performance scenario runner (`performance-§9`) — lives in `tests/` but is deliberately **outside the green gate**: it measures rather than verifies, and it asserts nothing about wall-clock time. **Do not** run it as part of the battery, count its scenarios as test cases, or fold its numbers into the pass/fail summary. If it exists, note in one line that it is available (`lua tests/perf.lua`) and move on. Same for any other runner the addon documents as non-gating.

**Not a suite: the complexity report.** `lizard` and the `docs/complexity.md` it produces are **not** part of this battery, and adding them would be a standards violation rather than a thoroughness win. The report's checkpoint is **release, not commit** (`performance-§10`), and it MUST NOT gate commits — a complexity threshold that fails a run teaches everyone to reach for `--no-verify`, after which the gate protects nothing and the habit remains. Do not run `lizard` here, do not report a stale `docs/complexity.md` as a red suite, and do not offer to regenerate it: that happens at release, in `/wow-addon:bump-version`.

Run suites read-only — none of this edits addon code.

## Step 2 — Combined summary

Print a compact summary:
- One line per suite: name — **pass / fail / skipped** — counts (e.g. `luacheck — pass — 0 warnings`, `tests/ — fail — 13 passed, 1 failed`).
- A headline verdict (e.g. `2/3 suites passed` or `All suites passed`).
- For failures, show the **relevant failing output** — the failed assertions / lint lines — not the entire log.

**Surface a kit-sync failure distinctly.** If the run includes a kit-sync / vendor-identity case — one asserting that the vendored `tests/_kit/` is byte-identical to its source `testkit/`, or that a vendored `libs/<Lib>/` matches its library repo's ship folder — and it fails, **do not report it as just another red assertion**. It is the one failure whose meaning is *"the copy in this repo has drifted from the library it came from"*, and it is otherwise invisible: both repos stay green while the copies diverge, because each suite tests its own copy. Call it out on its own line, name the files that differ, and state the remediation: **re-vendor the whole folder from the library repo** — not edit the vendored copy, not edit the test. If the check reports that it *could not run* (empty listing, source repo not found), treat that as a failure too, not a skip: a gate that goes quiet when it cannot look is worse than no gate.

If **no** suites were found at all, tell the user the addon has no test battery yet and point them at the Ka0s standard's headless `tests/` harness (`/wow-addon:new-addon` scaffolds one).

## Step 3 — On failure, offer to fix

If any suite failed, after printing the summary ask:

> "Want me to diagnose and fix the N failure(s)? (y/n)"

- **y** → investigate the failures, propose fixes, and apply them **with approval before editing** any file. Re-run the affected suite(s) to confirm. If a fix moves the addon's pass count, the standard requires the generated test-case inventory and the README test badge to move **in the same change** — regenerate the inventory with the runner's non-executing list mode and update the badge, rather than leaving it as a follow-up.
- **n** → stop. The user handles it.

## Hard rules

- **Read-only during the run.** The only time this command edits code is the opt-in fix phase in Step 3, after the user says yes.
- **Vendored folders are never edited — not even to make a test pass.** `libs/` and `tests/_kit/` are copies of code that lives in another repo; the next re-vendor overwrites any local patch silently, and the behavior it fixed returns as a regression with no cause anywhere in this repo's history. In the Step 3 fix phase, a failure whose real cause is in vendored code is an **upstream** fix plus a **re-vendor**, and this command's job is to say so clearly and stop — not to patch under `libs/` or `tests/_kit/`, and not to weaken or delete the test that caught it.
- **A missing tool is a skip, not a failure.** Don't report `luacheck`/interpreter absence as a red test result — report it as skipped with an install hint.
- **Don't dump full logs.** Show the failing lines; summarize the rest.
- **Don't fabricate results.** If a suite can't run, say why; never report a pass you didn't observe.

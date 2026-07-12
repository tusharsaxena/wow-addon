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
2. **tests/ harness (headless Lua unit tests)** — the Ka0s standard's headless Lua 5.1 harness. Discover the runner (in order of preference): an explicit entry like `tests/run_tests.lua` / `tests/run.lua`, else `*_test.lua` / `*_spec.lua` files under `tests/`. Pick an interpreter, preferring `lua5.1` → `lua` → `luajit`. Run the harness and capture its pass/fail counts. If a `tests/` dir exists but no interpreter is found, mark **skipped** with the reason.
3. **Makefile `test` target** — if a root `Makefile` defines a `test:` target, it is often the canonical entry point that already wraps lint + unit tests. **De-dup:** if `make test` clearly runs the same suites as 1–2, run `make test` **instead of** re-running those suites, and say so in the summary. If it does something additional (e.g. integration tests), run it as its own suite.

Run suites read-only — none of this edits addon code.

## Step 2 — Combined summary

Print a compact summary:
- One line per suite: name — **pass / fail / skipped** — counts (e.g. `luacheck — pass — 0 warnings`, `tests/ — fail — 13 passed, 1 failed`).
- A headline verdict (e.g. `2/3 suites passed` or `All suites passed`).
- For failures, show the **relevant failing output** — the failed assertions / lint lines — not the entire log.

If **no** suites were found at all, tell the user the addon has no test battery yet and point them at the Ka0s standard's headless `tests/` harness (`/wow-addon:new-addon` scaffolds one).

## Step 3 — On failure, offer to fix

If any suite failed, after printing the summary ask:

> "Want me to diagnose and fix the N failure(s)? (y/n)"

- **y** → investigate the failures, propose fixes, and apply them **with approval before editing** any file. Re-run the affected suite(s) to confirm.
- **n** → stop. The user handles it.

## Hard rules

- **Read-only during the run.** The only time this command edits code is the opt-in fix phase in Step 3, after the user says yes.
- **A missing tool is a skip, not a failure.** Don't report `luacheck`/interpreter absence as a red test result — report it as skipped with an install hint.
- **Don't dump full logs.** Show the failing lines; summarize the rest.
- **Don't fabricate results.** If a suite can't run, say why; never report a pass you didn't observe.

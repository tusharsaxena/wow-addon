---
description: Run the wow-addon:review subagent — a principal-engineer-level review of the addon in cwd. Re-runs the out-of-game suites first (luacheck, the test harness and its inventory, tests/perf.lua, lizard) so findings rest on today's numbers. Produces 01_FINDINGS.md, 02_PROPOSED_CHANGES.md, 03_SMOKE_TESTS.md, 04_EXECUTION_PLAN.md, and 05_FINAL_SUMMARY.md under docs/reviews/<YYYY-MM-DD>/, plus a chat summary.
---

Invoke the `wow-addon:review` subagent on the addon in the current working directory.

Use the Task tool with `subagent_type: "wow-addon:review"`. Pass through `$ARGUMENTS` verbatim as additional context for the reviewer if non-empty; otherwise instruct the agent to review the full addon at cwd.

The agent's first step is **measurement**: it re-runs every suite that works outside the game client — `luacheck`, the headless `tests/` harness plus a fresh `--list` inventory, the offline `tests/perf.lua` scenarios, `lizard` to a scratch path, a `Makefile` `test` target, and a vendored-copy `diff` — and reviews against those results rather than the committed `docs/test-cases.md`, `docs/automated-tests/RESULTS.md` or `docs/performance.md`. Don't pre-run any of them here or hand the agent numbers from earlier in the session; a stale figure passed in is exactly what the step exists to prevent. Anything needing a login stays out of it and lands in `03_SMOKE_TESTS.md` for a human.

Do not perform the review yourself in the main thread — delegate fully to the subagent so its findings, proposed changes, and execution plan are written to disk under `docs/reviews/<YYYY-MM-DD>/` per the agent's spec. After the agent returns, surface its chat summary verbatim to the user.

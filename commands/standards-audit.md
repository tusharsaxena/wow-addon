---
description: Run the wow-addon:standards-audit subagent — a read-only compliance audit of the addon in cwd against the living Ka0s WoW Addon Standard. Fetches the AUDIT.md playbook + standards/STANDARDS.md (the standard's index, then every section file it lists) from the WowAddonStandards repo at runtime and writes a frozen dated bundle to docs/audits/<YYYY-MM-DD>/ (01_CURRENT_STATE, 02_DEVIATIONS, 03_EVIDENCE, 04_TECHNICAL_DESIGN, 05_EXECUTION_PLAN), plus a chat summary.
---

Invoke the `wow-addon:standards-audit` subagent on the addon in the current working directory.

Use the Task tool with `subagent_type: "wow-addon:standards-audit"`. Pass through `$ARGUMENTS` verbatim as additional context for the auditor if non-empty (e.g. a subtree to focus on, or a note about an in-progress prior run); otherwise instruct the agent to audit the full addon at cwd.

The shared subsystems — debug console, options toolkit, slash dispatcher, performance harness, test framework — are `LibKa0s` modules, not addon code. Consuming the library is the compliant state; hand-rolling it is the deviation. If the agent's summary reads as though the addon is "missing" a console, an options toolkit or a dispatcher, that is the classic false positive: what the addon owns is a descriptor plus a degradation stub in its setup file, and the agent should have audited those. Say so and have it re-check rather than passing the finding on.

Do not perform the audit yourself in the main thread — delegate fully to the subagent so it fetches the current standard, follows the `AUDIT.md` playbook to the letter, and writes the frozen `docs/audits/<YYYY-MM-DD>/` bundle per its spec. The audit is read-only; it must not modify addon code. After the agent returns, surface its chat summary verbatim to the user.

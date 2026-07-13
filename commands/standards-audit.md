---
description: Run the wow-addon:standards-audit subagent — a read-only compliance audit of the addon in cwd against the living Ka0s WoW Addon Standard. Fetches the AUDIT.md playbook + standards/01_STANDARD.md from the WowAddonStandards repo at runtime and writes a frozen dated bundle to docs/audits/<YYYY-MM-DD>/ (01_CURRENT_STATE, 02_DEVIATIONS, 03_EVIDENCE, 04_TECHNICAL_DESIGN, 05_EXECUTION_PLAN), plus a chat summary.
---

Invoke the `wow-addon:standards-audit` subagent on the addon in the current working directory.

Use the Task tool with `subagent_type: "wow-addon:standards-audit"`. Pass through `$ARGUMENTS` verbatim as additional context for the auditor if non-empty (e.g. a subtree to focus on, or a note about an in-progress prior run); otherwise instruct the agent to audit the full addon at cwd.

Do not perform the audit yourself in the main thread — delegate fully to the subagent so it fetches the current standard, follows the `AUDIT.md` playbook to the letter, and writes the frozen `docs/audits/<YYYY-MM-DD>/` bundle per its spec. The audit is read-only; it must not modify addon code. After the agent returns, surface its chat summary verbatim to the user.

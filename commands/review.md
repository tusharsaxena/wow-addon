---
description: Run the wow-addon:review subagent — a principal-engineer-level review of the addon in cwd. Produces REVIEW_FINDINGS.md, REVIEW_PROPOSED_CHANGES.md, and REVIEW_EXECUTION_PLAN.md under reviews/<YYYY-MM-DD>/, plus a chat summary.
---

Invoke the `wow-addon:review` subagent on the addon in the current working directory.

Use the Task tool with `subagent_type: "wow-addon:review"`. Pass through `$ARGUMENTS` verbatim as additional context for the reviewer if non-empty; otherwise instruct the agent to review the full addon at cwd.

Do not perform the review yourself in the main thread — delegate fully to the subagent so its findings, proposed changes, and execution plan are written to disk under `reviews/<YYYY-MM-DD>/` per the agent's spec. After the agent returns, surface its chat summary verbatim to the user.

---
description: List the GitHub issues open on the current addon's repo, via the gh CLI. Optionally filter by label, or switch to closed/all. Read-only — never creates, edits, or closes issues.
argument-hint: [label to filter by] | [closed | all]  (optional; default: open)
allowed-tools: [Bash]
---

List the open GitHub issues for the repo at the cwd, using the `gh` CLI.

## Step 0 — Preflight

Run, and stop with clear guidance if either fails:

1. `gh auth status` — confirm `gh` is installed and authenticated. If not, tell the user to install `gh` and run `gh auth login`, then stop.
2. `gh repo view --json nameWithOwner` — confirm the cwd repo has a GitHub remote `gh` can resolve. If it can't (no remote, not a GitHub repo), say so and stop.

## Step 1 — Parse the argument

Parse `$ARGUMENTS` (trimmed):

- Empty → list **open** issues (default).
- `closed` → list closed issues. `all` → list open + closed.
- Anything else → treat it as a **label filter** on open issues (e.g. `bug`, `enhancement`).

## Step 2 — Fetch

Fetch as JSON for reliable parsing (do not screen-scrape the plain output):

```
gh issue list --state <state> --limit 100 --json number,title,labels,author,createdAt,url [--label "<label>"]
```

Use `--label` only when Step 1 produced a label filter.

## Step 3 — Report

Print a table sorted by issue number (descending, newest first):

| # | Title | Labels | Author | Age |
|---|-------|--------|--------|-----|

- **Age** = how long ago it was opened, humanized (e.g. `3d`, `2mo`).
- Above the table, state the count and scope (e.g. "**7 open issues**" or "**3 open issues labeled `bug`**").
- Below the table, list the issue URLs so they're clickable.
- If there are none, say so plainly (e.g. "No open issues.").

## Hard rules

- **Read-only.** Never run `gh issue create`, `gh issue close`, `gh issue edit`, or any mutation. This command only lists.
- **Don't paginate silently past 100.** If the repo has more than 100 matching issues, say the list is capped and how to narrow it (e.g. by label).

---
description: List the GitHub issues on the current addon's repo, via the gh CLI. Optionally filter by status prefix (untriaged / deferred / done / will-not-do) or by label, or switch to closed/all. Read-only — never creates, edits, or closes issues.
argument-hint: [untriaged | deferred | done | will-not-do] | [label] | [closed | all]  (optional; default: open)
allowed-tools: [Bash]
---

List the GitHub issues for the repo at the cwd, using the `gh` CLI.

## The `[status]` title prefix

Issues on a Ka0s addon repo are the durable store of pending work — `docs/pending/LEDGER.md` is retired and `/wow-addon:issue-audit` reads and writes this store. Status is carried as a **title prefix**, exactly `[<Status>] <Title>`:

| Prefix | Meaning | Issue state |
|---|---|---|
| `[untriaged]` | Seen and recorded; nobody has been asked about it yet | open |
| `[deferred]` | Decided: not now. Still on the books | open |
| `[done]` | Implemented | closed |
| `[will-not-do]` | Decided it will never be done | closed |

**Every issue always carries one of these four**, so a missing prefix is a defect rather than a fifth state. This command is a plain listing and deliberately does **not** repair it: show the issue with `—` in the Status column, say plainly that its prefix is missing, and point at `/wow-addon:issue-audit` or `/wow-addon:issue-triage`, which repair strays on sight. Don't guess a status for it, and don't fix it here — a listing that edits what it lists is a surprise nobody asked for.

For status, description and age together rather than a bare listing, use `/wow-addon:issue-details`; for counts across repos, `/wow-addon:issue-summary`.

**GitHub API guardrail.** Use the `gh` CLI subcommands — here that is `gh issue list` and, if a single issue needs expanding, `gh issue view` — with `--json` for structured data. **Never use `gh api graphql`** for issue work, and never hand-roll GraphQL queries against `api.github.com/graphql` — reaching for GraphQL first is a real, observed failure that wastes a round trip on a deprecated path before falling back. If a REST call is genuinely unavoidable, use `gh api repos/{owner}/{repo}/issues` — never the GraphQL endpoint. Because status lives in the title prefix, **filtering by status is a title filter you apply to the `gh issue list --json number,title,state` result yourself** — it is not a label query, not `--search`, and not a GraphQL search.

## Step 0 — Preflight

Run, and stop with clear guidance if either fails:

1. `gh auth status` — confirm `gh` is installed and authenticated. If not, tell the user to install `gh` and run `gh auth login`, then stop.
2. `gh repo view --json nameWithOwner` — confirm the cwd repo has a GitHub remote `gh` can resolve. If it can't (no remote, not a GitHub repo), say so and stop.

## Step 1 — Parse the argument

Parse `$ARGUMENTS` (trimmed), in this order:

- Empty → list **open** issues (default).
- `closed` → closed issues. `all` → open + closed.
- One of `untriaged`, `deferred`, `done`, `will-not-do` (with or without brackets) → a **status filter**. Fetch with `--state all` and then keep only issues whose title starts with that prefix — `done` and `will-not-do` live in the closed set, so filtering an open-only fetch by them silently returns nothing.
- Anything else → a **label filter** on open issues (e.g. `bug`, `enhancement`).

Status filters and label filters don't combine; if the user gives both, honour the status filter and say the label was ignored.

## Step 2 — Fetch

Fetch as JSON for reliable parsing (do not screen-scrape the plain output):

```
gh issue list --state <state> --limit 100 --json number,title,state,labels,author,createdAt,url [--label "<label>"]
```

Use `--label` only when Step 1 produced a label filter. Apply any status filter to the returned titles yourself — never as a `--search` or GraphQL query.

## Step 3 — Report

Print a table sorted by issue number (descending, newest first):

| # | Status | Title | State | Labels | Author | Age |
|---|--------|-------|-------|--------|--------|-----|

- **Status** = the title prefix without brackets (`untriaged`, `deferred`, `done`, `will-not-do`), or `—` when the issue carries none.
- **Title** = the title with the prefix stripped, so the column stays readable.
- **State** = `open` / `closed`. Show it whenever the scope can contain both; a `[deferred]` issue that is closed is an inconsistency worth seeing.
- **Age** = how long ago it was opened, humanized (e.g. `3d`, `2mo`).
- Above the table, state the count and scope (e.g. "**7 open issues**", "**3 open issues labeled `bug`**", "**4 `[deferred]` issues**").
- When the scope is broad enough to be worth it, add a one-line status tally under the count: `untriaged 5 · deferred 4 · done 12 · will-not-do 3`.
- Below the table, list the issue URLs so they're clickable.
- If there are none, say so plainly (e.g. "No open issues.", "No `[deferred]` issues.").

## Hard rules

- **Read-only.** Never run `gh issue create`, `gh issue close`, `gh issue edit`, `gh issue comment`, or any mutation. This command only lists. In particular, never "tidy up" a missing or malformed status prefix — report it, leave it.
- **Never use `gh api graphql`** or a hand-rolled GraphQL query. `gh issue list --json` is the whole surface this command needs.
- **Don't paginate silently past 100.** If the repo has more than 100 matching issues, say the list is capped and how to narrow it (by status or by label).

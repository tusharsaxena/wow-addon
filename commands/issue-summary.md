---
description: Collection-wide GitHub issue summary across every Ka0s addon and the three upstreams (WowAddonStandards, LibKa0s, wow-addon). Prints a status × repo grid, then lists the open issues per repo. Read-only. Pass a repo name to scope it to one.
argument-hint: [repo name]  (optional; default: the whole collection)
allowed-tools: [Bash, Read]
---

Report the state of pending work across the Ka0s collection by reading GitHub issues. This is the
companion to `/wow-addon:issue-audit`: that command *decides* things one repo at a time, this one
*shows you* where everything stands across all of them at once.

Read-only. This command never creates, edits, closes or comments on anything.

## Step 0 — Preflight

1. `gh auth status` — confirm `gh` is installed and authenticated. If not, tell the user to install
   `gh` and run `gh auth login`, then stop.

Issue work goes through the **`gh` CLI subcommands** — here that is `gh issue list` with `--json`.
**Never use `gh api graphql`** or a hand-rolled query against `api.github.com/graphql`: agents reach
for GraphQL first, spend a round trip on a deprecated path, and fall back to the subcommand that
would have worked. Because status is carried in the **title**, every count below is a title filter
over `gh issue list --json number,title,state`, not a label query and not a search.

## Step 1 — Resolve the roster

**Default (no `$ARGUMENTS`): the whole collection.** Read the roster rather than hardcoding it —
`WowAddonStandards/standards/ADDONS.md` carries the addon table (folder + repository URL per row)
and is the living list. Take the addon repos from there, then add the three upstreams:

- **`WowAddonStandards`** — the standard itself
- **`LibKa0s`** — the shared library
- **`wow-addon`** — this plugin

If `ADDONS.md` isn't reachable (the sibling repo isn't checked out), fall back to the sibling
directories next to the cwd that contain a `.toc`, and **say in the report** that the roster was
inferred from disk rather than read from the standard — an inferred roster can silently omit a repo,
and a missing repo in a collection-wide report reads as "no open issues" rather than "not checked".

**With `$ARGUMENTS`:** treat it as a single repo name and scope everything to it. Match
case-insensitively against the roster; if it matches nothing, say so, list the valid names, and stop.
Don't guess at a near-miss — reporting the wrong repo's issues silently is worse than asking.

## Step 2 — Fetch

For each repo in the roster, one call:

```
gh issue list -R <owner>/<repo> --state all --limit 500 --json number,title,state,labels,createdAt,url
```

- A repo that has no GitHub remote, doesn't exist, or that `gh` can't read is **not** a zero — record
  it as **unreadable** and carry that through to the report as its own state. A permission error
  rendered as `0` is a wrong answer, not a tidy one.
- If any repo hits the `--limit`, say so rather than reporting a truncated count.
- Space the calls out slightly; this is a read sweep over a dozen repos, not a burst of writes.

## Step 3 — Classify

Every issue falls in exactly one column, taken from its **title prefix**:

| Column | Title prefix | Expected state |
|---|---|---|
| `done` | `[done]` | closed |
| `will-not-do` | `[will-not-do]` | closed |
| `deferred` | `[deferred]` | open |
| `untriaged` | `[untriaged]` | open |
| `unprefixed` | *(none)* | usually open |

Match the prefix case-insensitively at the very start of the title. An issue whose title carries no
recognised prefix goes in **`unprefixed`** — that column is the useful one: it is exactly the work
that `/wow-addon:issue-audit` has never triaged.

**Report any prefix/state disagreement** — a `[deferred]` issue that is closed, a `[done]` issue that
is open — as a short **Inconsistencies** list under the grid, with repo, number and both values. The
prefix and the open/closed state encode the same decision twice, so a disagreement means one of them
is wrong and a human has to say which. Don't fix them and don't count them twice; just surface them.

## Step 4 — The grid

Rows are repos, columns are the five statuses, plus a total. Addons first in roster order, then the
three upstreams, then a totals row:

| Repo | done | will-not-do | deferred | untriaged | unprefixed | Total |
|---|---|---|---|---|---|---|

- Right-align the numbers. Write `0` as `—` so the populated cells carry the eye.
- An unreadable repo gets a single `unreadable` spanning its row rather than five zeros.
- Under the grid state the collection totals in one line: how many issues, how many **open**, and how
  many of those open ones are `unprefixed` (i.e. never triaged).

## Step 5 — Open issues per repo

Then, for each repo **in roster order**, list only its **OPEN** issues:

### <Repo>  — N open

| # | Status | Title | Age |
|---|---|---|---|

- **Status** is the prefix column (`deferred`, `untriaged`, `unprefixed`).
- **Title** is the title with the prefix stripped — the prefix is already in its own column, and
  repeating it wastes the width that the actual title needs.
- **Age** is how long ago it was opened, humanized (`3d`, `2mo`).
- Sort by status (`untriaged` and `unprefixed` first — they're the ones needing a decision), then by
  number descending.
- A repo with no open issues gets one line: `**<Repo>** — no open issues.` Don't print an empty table.
- Put the issue URLs under each table so they're clickable.

## Step 6 — Close

End with the single most useful sentence the data supports — e.g. which repo carries the most
untriaged work, or that everything is triaged. Say it plainly; don't editorialize, and don't invent a
recommendation the numbers don't support.

## Hard rules

- **Read-only.** Never run `gh issue create`, `gh issue edit`, `gh issue close`, `gh issue comment`,
  or any other mutation. This command only reads and reports.
- **Never use `gh api graphql`.** Use the `gh issue` subcommands with `--json`.
- **Never report an unreadable repo as zero.** Unreadable and empty are different answers, and
  collapsing them hides exactly the repo someone needs to look at.
- **Don't infer status from labels.** The title prefix is the data; a label named `deferred` is not.
- **Don't invent the roster.** Read it from `ADDONS.md`, or say plainly that you inferred it.

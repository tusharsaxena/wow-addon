---
description: GitHub issue summary — a status × repo grid (done / will-not-do / deferred / untriaged) followed by the open issues per repo. Defaults to the repo at the cwd; pass `all` for the whole collection (every Ka0s addon plus WowAddonStandards, LibKa0s and wow-addon) or a repo name. Read-only apart from repairing a missing title prefix.
argument-hint: [here|all|<repo>]
allowed-tools: [Bash, Read]
---

Report the state of pending work by reading GitHub issues, as counts. This is the wide view in the issue command family:

- `/wow-addon:issue-audit` — sweeps a repo and **files** what it finds as `[untriaged]`
- `/wow-addon:issue-triage` — **decides** the untriaged ones, one at a time
- `/wow-addon:issue-summary` — **how much, and where** (this command)
- `/wow-addon:issue-details` — **what**, item by item with descriptions

## Step 0 — Preflight

`gh auth status` — if `gh` is missing or unauthenticated, say so, tell the user to run `gh auth login`, and stop.

**GitHub API guardrail.** Issue work goes through the `gh` CLI subcommands — here that is `gh issue list` with `--json`. **Never use `gh api graphql`** or a hand-rolled query against `api.github.com/graphql`: agents reach for GraphQL first, spend a round trip on a deprecated path, and fall back to the subcommand that would have worked. Because status is carried in the **title**, every count below is a title filter over `gh issue list --json number,title,state`, not a label query and not a search.

## Step 1 — Resolve the scope

The `$ARGUMENTS` token:

- **absent, or `here`** → the repo at the cwd. **This is the default.**
- **`all`** → the whole collection. Read the addon roster from `WowAddonStandards/standards/ADDONS.md` (folder + repository per row) — it is the living list — then add the three upstreams: **`WowAddonStandards`**, **`LibKa0s`**, **`wow-addon`**.
- **a repo name** → that repo alone, matched case-insensitively against the roster. If it matches nothing, say so, list the valid names, and stop. Don't guess at a near-miss — reporting the wrong repo silently is worse than asking.

If `ADDONS.md` isn't reachable on an `all` run, fall back to the sibling directories next to the cwd that contain a `.toc`, and **say in the report that the roster was inferred from disk rather than read from the standard**. An inferred roster can silently omit a repo, and a missing repo in a collection-wide report reads as "no open issues" rather than "not checked".

If the cwd is not a repo `gh` can resolve and no scope was given, **ask** which scope to use rather than guessing.

## Step 2 — Fetch

For each repo in scope, one call:

```
gh issue list -R <owner>/<repo> --state all --limit 500 --json number,title,state,labels,createdAt,url
```

- A repo that has no GitHub remote, doesn't exist, or that `gh` can't read is **not** a zero — record it as **unreadable** and carry that through to the report as its own state. A permission error rendered as `0` is a wrong answer, not a tidy one.
- If any repo hits the `--limit`, say so rather than reporting a truncated count.
- On an `all` run, space the calls out slightly; this is a read sweep over a dozen repos.

## Step 3 — Classify

Every issue falls in exactly one column, taken from its **title prefix**, matched case-insensitively at the very start of the title:

| Column | Title prefix | Expected state |
|---|---|---|
| `done` | `[done]` | closed |
| `will-not-do` | `[will-not-do]` | closed |
| `deferred` | `[deferred]` | open |
| `untriaged` | `[untriaged]` | open |

**Every issue always carries one of these four.** There is no unprefixed column, because there is no unprefixed state — an issue that arrives without a prefix (filed from the GitHub web UI, or by someone not using these commands) is **repaired on sight**:

- open → `gh issue edit <n> --title "[untriaged] <existing title>"`
- closed → `[done]` if it was closed as completed, `[will-not-do]` if closed as not planned (`gh api repos/{owner}/{repo}/issues/<n>` reports `state_reason`)

Keep the original title text exactly — you are prefixing it, not rewriting somebody's words. **This is the only write this command makes, and every repair must appear in the report**, with the old and new title. A command people run to look at things must never change one quietly; announcing it is what keeps that true. If a repair fails, count the issue under `untriaged` anyway and say the title could not be fixed.

**Report any prefix/state disagreement** — a `[deferred]` issue that is closed, a `[done]` issue that is open — as a short **Inconsistencies** list under the grid, with repo, number and both values. The prefix and the open/closed state encode the same decision twice, so a disagreement means one of them is wrong and a human has to say which. Don't fix them, don't count them twice; surface them and point at `/wow-addon:issue-triage`.

## Step 4 — The grid

Rows are repos, columns are the four statuses, plus a total. On an `all` run: addons first in roster order, then the three upstreams, then a totals row. On a single-repo run it is one row and the totals line below carries the useful part.

| Repo | done | will-not-do | deferred | untriaged | Total |
|---|---:|---:|---:|---:|---:|

- Right-align the numbers. Write `0` as `—` so the populated cells carry the eye.
- An unreadable repo gets a single `unreadable` spanning its row rather than four zeros.
- Under the grid, state the totals in one line: how many issues, how many **open**, and how many of those are `untriaged` — that last number is the backlog nobody has decided on, and it is the one worth reading first.

## Step 5 — Open issues per repo

Then, for each repo **in roster order**, list only its **OPEN** issues:

### <Repo> — N open

| # | Status | Title | Age |
|---|---|---|---|

- **Status** is `untriaged` or `deferred` (the only two open states).
- **Title** is the title with the prefix stripped — the prefix is already its own column.
- **Age** is how long ago it was opened, humanized (`3d`, `2mo`).
- Sort `untriaged` first — those are the ones needing a decision — then by number descending.
- A repo with no open issues gets one line: `**<Repo>** — no open issues.` Don't print an empty table.
- Put the issue URLs under each table so they're clickable.

For descriptions of each issue rather than just titles, that's `/wow-addon:issue-details`.

## Step 6 — Close

End with the single most useful sentence the data supports — which repo carries the most untriaged work, or that everything is triaged. Say it plainly; don't editorialize, and don't invent a recommendation the numbers don't support.

## Hard rules

- **Read-only, with exactly one exception:** repairing a missing title prefix. Never create, close, reopen or comment, and never edit a title's text or a body.
- **Announce every repair**, with old and new title.
- **Never use `gh api graphql`.** Use the `gh issue` subcommands with `--json`. `gh api repos/{owner}/{repo}/issues/<n>` is the sanctioned REST fallback for `state_reason`, which `gh issue view` does not expose on every `gh` version.
- **Never report an unreadable repo as zero.** Unreadable and empty are different answers, and collapsing them hides exactly the repo someone needs to look at.
- **Don't infer status from labels.** The title prefix is the data; a label named `deferred` is not.
- **Don't invent the roster.** Read it from `ADDONS.md`, or say plainly that you inferred it.

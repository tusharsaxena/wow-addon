---
description: GitHub issue counts — a status × repo grid (done / will-not-do / triaged / untriaged) plus a short read of what the numbers imply. **Defaults to the whole collection** (every Ka0s addon plus WowAddonStandards, LibKa0s and wow-addon); pass `here` for the repo at the cwd, or a repo name. Counts only — for the issues themselves use `/wow-addon:issue-details`. Read-only apart from repairing a missing title prefix.
argument-hint: [here|all|<repo>]
allowed-tools: [Bash, Read]
---

Report the state of pending work by reading GitHub issues, as counts. This is the wide view in the issue command family:

- `/wow-addon:issue-audit` — sweeps a repo and **files** what it finds as `[untriaged]`
- `/wow-addon:issue-triage` — **decides** the untriaged ones, one at a time
- `/wow-addon:issue-summary` — **how much, and where** (this command). Counts only; it never lists issues.
- `/wow-addon:issue-details` — **what**, item by item with descriptions

## Step 0 — Preflight

`gh auth status` — if `gh` is missing or unauthenticated, say so, tell the user to run `gh auth login`, and stop.

**GitHub API guardrail.** Issue work goes through the `gh` CLI subcommands — here that is `gh issue list` with `--json`. **Never use `gh api graphql`** or a hand-rolled query against `api.github.com/graphql`: agents reach for GraphQL first, spend a round trip on a deprecated path, and fall back to the subcommand that would have worked. Because status is carried in the **title**, every count below is a title filter over `gh issue list --json number,title,state`, not a label query and not a search.

## Step 1 — Resolve the scope

The `$ARGUMENTS` token:

- **absent, or `all`** → the whole collection. **This is the default.** Read the addon roster from `WowAddonStandards/standards/ADDONS.md` (folder + repository per row) — it is the living list — then add the three upstreams: **`WowAddonStandards`**, **`LibKa0s`**, **`wow-addon`**.
- **`here`** → the repo at the cwd.
- **a repo name** → that repo alone, matched case-insensitively against the roster. If it matches nothing, say so, list the valid names, and stop. Don't guess at a near-miss — reporting the wrong repo silently is worse than asking.

**Why the collection is the default here, when every other issue command defaults to `here`:** this is the only one whose whole value is the cross-repo comparison. A one-row grid is strictly worse than `/wow-addon:issue-details here`. It is also routinely run from an orchestration directory that is not itself a GitHub repo, where a `here` default cannot resolve at all and can only produce a question.

If `ADDONS.md` isn't reachable on an `all` run, fall back to the sibling directories next to the cwd that contain a `.toc`, and **say in the report that the roster was inferred from disk rather than read from the standard**. An inferred roster can silently omit a repo, and a missing repo in a collection-wide report reads as "no open issues" rather than "not checked".

If `here` was passed explicitly and the cwd is not a repo `gh` can resolve, say so and stop — the user named a scope that does not exist. This can no longer happen by default, since the default is `all`.

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
| `triaged` | `[triaged]` | open |
| `untriaged` | `[untriaged]` | open |

**Every issue always carries one of these four.** There is no unprefixed column, because there is no unprefixed state — an issue that arrives without a prefix (filed from the GitHub web UI, or by someone not using these commands) is **repaired on sight**:

- open → `gh issue edit <n> --title "[untriaged] <existing title>"`
- closed → `[done]` if it was closed as completed, `[will-not-do]` if closed as not planned (`gh api repos/{owner}/{repo}/issues/<n>` reports `state_reason`)

Keep the original title text exactly — you are prefixing it, not rewriting somebody's words. **This is the only write this command makes, and every repair must appear in the report**, with the old and new title. A command people run to look at things must never change one quietly; announcing it is what keeps that true. If a repair fails, count the issue under `untriaged` anyway and say the title could not be fixed.

**Report any prefix/state disagreement** — a `[triaged]` issue that is closed, a `[done]` issue that is open — as a short **Inconsistencies** list under the grid, with repo, number and both values. The prefix and the open/closed state encode the same decision twice, so a disagreement means one of them is wrong and a human has to say which. Don't fix them, don't count them twice; surface them and point at `/wow-addon:issue-triage`.

## Step 4 — The grid

Rows are repos, columns are the four statuses, plus a total. On an `all` run: addons first in roster order, then the three upstreams, then a totals row. On a single-repo run it is one row and the totals line below carries the useful part.

| Repo | done | will-not-do | triaged | untriaged | Total |
|---|---:|---:|---:|---:|---:|

- Right-align the numbers. Write `0` as `—` so the populated cells carry the eye.
- An unreadable repo gets a single `unreadable` spanning its row rather than four zeros.
- Under the grid, state the totals in one line: how many issues, how many **open**, and how many of those are `untriaged` — that last number is the backlog nobody has decided on, and it is the one worth reading first.

## Step 5 — Read the grid

**This command prints counts and what they mean. It does not list issues.** Per-issue tables — titles, descriptions, ages, URLs — are `/wow-addon:issue-details`, and duplicating them here would mean two commands doing the same job with the shorter one always out of date.

So after the grid, write a few sentences of analysis. Not a restatement of the numbers the reader can already see — the things the numbers *imply* that a column of totals does not show on its own:

- **Concentration.** Which repo carries a disproportionate share of the open work, and how disproportionate. One repo holding a third of the collection's open issues is a fact about that repo, not about the collection.
- **The `untriaged` count.** This is the backlog nobody has decided on and it is the first number worth reading. Say where it sits. Zero across the board is worth stating plainly — it means every open issue has a recorded decision behind it.
- **Shape of the closed work.** A repo whose `will-not-do` outnumbers its `done` is deciding more than it is building; the reverse is the opposite. Neither is wrong, and both are worth noticing.
- **Empty repos.** A repo with no issues at all is either genuinely clear or never swept. The grid cannot tell those apart, so say which one you can and cannot distinguish.
- **Movement**, only where you can source it — a figure from a previous run in this session, for instance. Never infer a trend from a single snapshot.

**Ground every observation in the grid.** If a claim cannot be checked against a number in the table above it, it does not belong here. No recommendations the counts do not support, no guesses about why a repo looks the way it does, and no advice about what to work on next — that is a judgment the reader makes with context this command does not have.

Keep it to a short paragraph or a few bullets. The grid is the deliverable; the analysis earns its place only by saying something the grid does not.

## Hard rules

- **Read-only, with exactly one exception:** repairing a missing title prefix. Never create, close, reopen or comment, and never edit a title's text or a body.
- **Never list issues.** No per-repo tables, no titles, no URLs. Counts and analysis only — `/wow-addon:issue-details` owns the per-issue view, and two commands printing the same listing means the shorter one silently goes stale.
- **Never assert what the grid cannot support.** Every sentence of analysis traces to a number in the table. No trends from one snapshot, no advice on what to work on next.
- **Announce every repair**, with old and new title.
- **Never use `gh api graphql`.** Use the `gh issue` subcommands with `--json`. `gh api repos/{owner}/{repo}/issues/<n>` is the sanctioned REST fallback for `state_reason`, which `gh issue view` does not expose on every `gh` version.
- **Never report an unreadable repo as zero.** Unreadable and empty are different answers, and collapsing them hides exactly the repo someone needs to look at.
- **Don't infer status from labels.** The title prefix is the data; a label named `triaged` is not.
- **Don't invent the roster.** Read it from `ADDONS.md`, or say plainly that you inferred it.

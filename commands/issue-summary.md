---
description: GitHub issue counts — a status × repo grid, a severity × repo grid over the open backlog, and a status × severity crosstab, plus a short read of what the numbers imply. **Defaults to the whole collection** (every Ka0s addon plus WowAddonStandards, LibKa0s and wow-addon); pass `here` for the repo at the cwd, or a repo name. Counts only — for the issues themselves use `/wow-addon:issue-details`. Read-only apart from repairing a missing status or severity label.
argument-hint: [here|all|<repo>]
allowed-tools: [Bash, Read]
---

Report the state of pending work by reading GitHub issues, as counts. This is the wide view in the issue command family:

- `/wow-addon:issue-audit` — sweeps a repo and **files** what it finds as `state:untriaged`
- `/wow-addon:issue-triage` — **decides** the untriaged ones, one at a time
- `/wow-addon:issue-summary` — **how much, how bad, and where** (this command). Counts only; it never lists issues.
- `/wow-addon:issue-details` — **what**, item by item with descriptions
- `/wow-addon:issue-fetch-all` — a plain listing of one repo
- `/wow-addon:issue-add` — files one new issue by hand

## Step 0 — Preflight

`gh auth status` — if `gh` is missing or unauthenticated, say so, tell the user to run `gh auth login`, and stop.

**GitHub API guardrail.** Issue work goes through the `gh` CLI subcommands — here that is `gh issue list` with `--json`. **Never use `gh api graphql`** or a hand-rolled query against `api.github.com/graphql`: agents reach for GraphQL first, spend a round trip on a deprecated path, and fall back to the subcommand that would have worked. Because status and severity are **labels**, every count below comes from the `labels` array on `gh issue list --json number,title,state,labels` — never from a title prefix, never from a `--search`.

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

Every issue is classified twice, both times from its **labels**:

**Status** — exactly one `state:` label:

| Column | Label | Expected GitHub state |
|---|---|---|
| `done` | `state:done` | closed |
| `will-not-do` | `state:will-not-do` | closed |
| `triaged` | `state:triaged` | open |
| `untriaged` | `state:untriaged` | open |

**Severity** — exactly one `severity:` label: `severity:critical`, `severity:high`, `severity:medium`, `severity:low`.

**Every issue always carries one of each.** There is no unlabelled column, because there is no unlabelled state — an issue that arrives without a `state:` label (filed from the GitHub web UI, or by someone not using these commands) is **repaired on sight**:

- open → `gh issue edit <n> --add-label "state:untriaged"`
- closed → `state:done` if it was closed as completed, `state:will-not-do` if closed as not planned (`gh api repos/{owner}/{repo}/issues/<n>` reports `state_reason`)

An issue with no `severity:` label is **not** repaired here. Severity is a judgment call that needs the body read against the ladder, and this command deliberately doesn't read bodies. Count it in a **`—` column** on the severity grid, say how many there are, and point at `/wow-addon:issue-audit`, which assigns one on sight. A guessed severity from a title alone would land in a grid people then reason from, and a fabricated number in a counts report is worse than a visible gap.

A **legacy `[status]` title prefix** is leftover text from the retired prefix scheme. If the label and the prefix disagree, the **label wins**. Don't strip the prefix here — that is a title edit, and this command's one sanctioned write is adding a missing status label. Note any issue where they disagree under *Inconsistencies*.

**This is the only write this command makes, and every repair must appear in the report**, with the issue number and the label added. A command people run to look at things must never change one quietly; announcing it is what keeps that true. If a repair fails, count the issue under `untriaged` anyway and say the label could not be added.

**Report any label/state disagreement** — a `state:triaged` issue that is closed, a `state:done` issue that is open, an issue carrying two `state:` labels — as a short **Inconsistencies** list under the grids, with repo, number and both values. The label and the open/closed state encode the same decision twice, so a disagreement means one of them is wrong and a human has to say which. Don't fix them, don't count them twice; surface them and point at `/wow-addon:issue-triage`.

## Step 4 — The grids

Three cuts, in this order. They answer different questions and none of them is derivable from another.

### 4a. Status × repo — how much, and where

| Repo | done | will-not-do | triaged | untriaged | Total |
|---|---:|---:|---:|---:|---:|

On an `all` run: addons first in roster order, then the three upstreams, then a totals row. On a single-repo run it is one row and the totals line below carries the useful part.

- Right-align the numbers. Write `0` as `—` so the populated cells carry the eye.
- An unreadable repo gets a single `unreadable` spanning its row rather than four zeros.

### 4b. Severity × repo, **open issues only** — how bad the live backlog is

| Repo | critical | high | medium | low | — | Open |
|---|---:|---:|---:|---:|---:|---:|

**Open only, and say so in the heading.** Closed issues are settled: the severity of something already done or already declined tells you nothing about what to do next, and folding it in lets a repo with a long `done` history look dangerous. The actionable question this grid answers is *how much of what is still on the books is serious*, and that question is about `state:untriaged` + `state:triaged` alone.

The `—` column is issues with no `severity:` label. Keep it even when it is empty on every row: a column that vanishes when the data is clean is a column nobody notices when the data isn't.

### 4c. Status × severity — where the serious work is stuck

One small crosstab over the **whole scope**, all repos combined:

| | critical | high | medium | low | — |
|---|---:|---:|---:|---:|---:|
| untriaged | | | | | |
| triaged | | | | | |
| done | | | | | |
| will-not-do | | | | | |

This is the cut that says something neither of the other two can. `untriaged × critical` is the cell to read first — serious work nobody has even been asked about. `triaged × critical` is the second: serious work someone consciously parked. `will-not-do × critical` deserves a sentence of its own if it is non-zero, because declining something graded critical is a real decision and it should not pass as a number in a table.

On a single-repo run this grid is still worth printing; it is the same shape and it is the whole report's payload once the per-repo dimension collapses.

### Under the grids

State the totals in one line: how many issues, how many **open**, how many of those are `state:untriaged`, and how many open issues are `critical` or `high`. Those last two numbers are the backlog nobody has decided on and the part of it that is serious, and they are the two worth reading first.

## Step 5 — Read the grids

**This command prints counts and what they mean. It does not list issues.** Per-issue tables — titles, descriptions, ages, URLs — are `/wow-addon:issue-details`, and duplicating them here would mean two commands doing the same job with the shorter one always out of date.

So after the grids, write a few sentences of analysis. Not a restatement of the numbers the reader can already see — the things the numbers *imply* that a column of totals does not show on its own:

- **Concentration.** Which repo carries a disproportionate share of the open work, and how disproportionate. One repo holding a third of the collection's open issues is a fact about that repo, not about the collection.
- **Severity concentration is a different fact from volume.** A repo with four open issues, two of them `high`, is in worse shape than one with twenty `low`. Say so where the grids show it, and say so explicitly when volume and severity point at different repos — that divergence is the single most useful thing these two grids produce together.
- **The `untriaged` count**, and how much of it is serious. This is the backlog nobody has decided on and it is the first number worth reading. Zero across the board is worth stating plainly — it means every open issue has a recorded decision behind it.
- **Anything critical or high that is `triaged` rather than open work.** Something graded serious and consciously parked is the collection's most interesting row, in either direction: either the grade is wrong or the parking is.
- **Shape of the closed work.** A repo whose `will-not-do` outnumbers its `done` is deciding more than it is building; the reverse is the opposite. Neither is wrong, and both are worth noticing.
- **Unlabelled severity.** A large `—` column means the backlog has not been sized, so the severity grid is measuring less than it appears to. Say how much of it is unsized before drawing any conclusion from it.
- **Empty repos.** A repo with no issues at all is either genuinely clear or never swept. The grid cannot tell those apart, so say which one you can and cannot distinguish. A repo with no `state:` labels at all has never been swept — that one the grid *can* tell you.
- **Movement**, only where you can source it — a figure from a previous run in this session, for instance. Never infer a trend from a single snapshot.

**Ground every observation in the grids.** If a claim cannot be checked against a number in a table above it, it does not belong here. No recommendations the counts do not support, no guesses about why a repo looks the way it does, and no advice about what to work on next — that is a judgment the reader makes with context this command does not have.

Keep it to a short paragraph or a few bullets. The grids are the deliverable; the analysis earns its place only by saying something they do not.

## Hard rules

- **Read-only, with exactly one exception:** adding a missing `state:` label. Never create, close, reopen or comment, never edit a title or a body, and **never assign a severity** — that needs the body read and belongs to `/wow-addon:issue-audit`.
- **Never list issues.** No per-repo tables of titles, no URLs. Counts and analysis only — `/wow-addon:issue-details` owns the per-issue view, and two commands printing the same listing means the shorter one silently goes stale.
- **The severity grid is open-only.** Folding closed issues into it makes a well-maintained repo look dangerous and is the one way these grids can actively mislead.
- **Never assert what the grids cannot support.** Every sentence of analysis traces to a number in a table. No trends from one snapshot, no advice on what to work on next.
- **Announce every repair**, with the issue number and the label added.
- **Never use `gh api graphql`.** Use the `gh issue` subcommands with `--json`. `gh api repos/{owner}/{repo}/issues/<n>` is the sanctioned REST fallback for `state_reason`, which `gh issue view` does not expose on every `gh` version.
- **Never report an unreadable repo as zero.** Unreadable and empty are different answers, and collapsing them hides exactly the repo someone needs to look at.
- **Never infer status or severity from the title.** The labels are the data; a leftover `[triaged]` prefix is stale text, and a title that sounds alarming is not a `severity:critical`.
- **Never hide the `—` column.** An unsized backlog is a finding, not a rounding error.
- **Don't invent the roster.** Read it from `ADDONS.md`, or say plainly that you inferred it.

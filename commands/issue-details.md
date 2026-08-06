---
description: List the addon's GitHub issues with their status and a one-line description of each. Defaults to what is still live — `[untriaged]` and `[triaged]`. Pass states to widen it (`done`, `will-not-do`, `all`), and a scope to change repo. The detail view to `/wow-addon:issue-summary`'s counts.
argument-hint: [here|all|<repo>] [untriaged|triaged|done|will-not-do|open|closed|all]
allowed-tools: [Bash, Read]
---

Show what is actually in the issue store, item by item, with enough of each to recognise it without opening GitHub.

This is the companion to `/wow-addon:issue-summary`: that one answers *how much and where*, this one answers *what*. Where summary prints a grid of counts across repos, this prints the issues themselves.

## Step 0 — Preflight

`gh auth status` — if `gh` is missing or unauthenticated, say so, tell the user to run `gh auth login`, and stop.

**GitHub API guardrail.** Use `gh issue list` with `--json`. **Never use `gh api graphql`** or a hand-rolled query against `api.github.com/graphql`. Status lives in the **title prefix**, so filtering by status is a title filter over the JSON — not a label query and not a search.

## Step 1 — Resolve the scope

The **first** `$ARGUMENTS` token, if it is a scope keyword:

- **absent, or `here`** → the repo at the cwd. **This is the default.**
- **`all`** → every addon repo plus the three upstreams (`WowAddonStandards`, `LibKa0s`, `wow-addon`). Read the addon roster from `WowAddonStandards/standards/ADDONS.md`; if unreachable, fall back to sibling directories with a `.toc` and **say the roster was inferred** — an inferred roster can silently omit a repo, and a missing repo reads as "nothing here" rather than "not checked".
- **a repo name** → that repo alone, matched case-insensitively against the roster. No match → say so, list the valid names, and stop. Don't guess at a near-miss.

If the cwd is not a repo `gh` can resolve and no scope was given, **ask** which scope to use rather than guessing.

## Step 2 — Resolve the states

The remaining token(s) select which statuses to show. Accept them comma- or space-separated.

- **absent** → **`untriaged` + `triaged`**. This is the default and it is deliberate: those two are the live store — everything still awaiting a decision or awaiting the work. The terminal states are history, and printing 150 closed issues by default would bury the 20 that need you.
- **`open`** → same as the default (`untriaged` + `triaged`)
- **`closed`** → `done` + `will-not-do`
- **`all`** → all four
- **any of `untriaged`, `triaged`, `done`, `will-not-do`** → exactly those, in any combination

An unrecognised token is an error, not a filter — say so and list the valid values rather than silently returning everything.

## Step 3 — Fetch

Per repo in scope:

```
gh issue list -R <owner>/<repo> --state all --limit 500 --json number,title,state,body,labels,createdAt,updatedAt,url
```

- A repo `gh` cannot read is **unreadable**, not empty. Carry that through to the output as its own state — a permission error rendered as "no issues" is a wrong answer wearing a tidy hat.
- If a repo hits the limit, say so rather than reporting a truncated list.
- Space the calls out slightly on a wide scope.

## Step 4 — Classify and describe

Take each issue's status from its **title prefix**, matched case-insensitively at the very start. Strip the prefix from the displayed title — it has its own column and repeating it wastes the width the title needs.

**An issue with no recognised prefix is repaired on sight**, because every issue in this store always carries one: `gh issue edit <n> --title "[untriaged] <existing title>"`, keeping the original text exactly. This is the **only** write this command makes. State it in the output every time it happens — a read command that silently changes something is worse than one that doesn't repair at all. If the repair fails, show the issue as `untriaged` anyway and say the title could not be fixed.

For each issue produce a **one-line description**: the single most useful sentence about what it is. Take it from the body — the `Evidence` block, the first line of `Rationale`, or the first substantive sentence — and compress to the Step 5 width budget (≤ 36 characters at the current roster — see *Row width* below, and recompute if the roster changes). **Never invent it**; if the body has nothing usable, write `—` rather than restating the title back in different words. A description that just paraphrases the title is noise pretending to be information.

## Step 5 — Print

Per repo, in roster order, one section each:

### <Repo> — N issues (<states shown>)

| # | Status | Title | Description | Age | URL |
|---|---|---|---|---|---|

- **Status** is the prefix (`untriaged`, `triaged`, `done`, `will-not-do`).
- **Age** is time since it was opened, humanized (`3d`, `2mo`).
- **`State` is a conditional column, not a permanent one.** GitHub's `open`/`closed` is implied by the status for every well-formed issue, so a permanent column spends width on a value the reader can already infer. Add it **only** for a repo that actually contains a prefix/state disagreement, and only to that repo's table. Otherwise the disagreements are reported in the Inconsistencies list below and the column is pure cost.
- **URL** is the issue's full `https://github.com/<owner>/<repo>/issues/<n>`, **last column, one per row**. Write it bare — no markdown link wrapper, no shortening, no `…` truncation — because the point of this column is that a terminal can detect it and make it clickable, and every one of those transformations breaks that.
- Sort by status — `untriaged` first, then `triaged`, then `done`, then `will-not-do` — and within each, by number descending. Untriaged first because it is the only status that means *nobody has looked at this*.
- A repo with nothing matching gets one line: `**<Repo>** — no issues matching <states>.` Don't print an empty table.

**The URL goes in the row, not in a list underneath.** A list below the table makes the reader match a number to a link by eye, which is exactly the step the column removes. It also means the row and its link can never drift apart when the table is sorted or filtered.

### Row width is a correctness constraint, not a style preference

A full issue URL runs to **58 characters** for the longest repo name in the collection and cannot be shortened, so everything else is budgeted around it. Do the arithmetic rather than eyeballing it:

```
7 pipes + 12 padding spaces +  2 (number) + 9 ("untriaged") + 5 (age) + 58 (URL)  =  93 fixed
```

**93 characters are gone before a single character of Title or Description.** So:

| Row budget | Left for Title + Description |
|---|---|
| 140 | 47 — **unusable**, ~23 each |
| 160 | 67 |
| **170** | **77 — the working target** |
| 180 | 87 |

**Target ~170 characters: Title ≤ 40, Description ≤ 36**, truncating with a trailing `…`.

This is not tidiness. A terminal that renders markdown tables as box drawing **mangles rows past its width** — it clips them, and when it does it can lose the association between a row and its header, so a row from one repo appears under another repo's heading with no header line at all. A reader then trusts a table that is silently lying about which repo they are looking at. Measured on a real 72-issue run: rows reached **207 characters**, 61 of 92 exceeded 160, and that run produced exactly that failure.

If something has to give, **compress the Description, never the URL** — a shortened description is still useful, a shortened URL is not a link. If even that is not enough, narrow the scope to fewer repos or use `/wow-addon:issue-summary`; do not widen the table.

**Do not set a budget you have not checked.** The 93-character floor moves with the longest repo name in scope, so recompute it rather than copying the numbers above when the roster changes.

**Escape pipes.** Any `|` inside a title or description must be written `\|`, or it splits the row into extra cells and corrupts every column after it.

### The rendered report belongs in the reply, not in tool output

**Markdown only renders in the assistant's reply.** Inside a command-output block it is displayed raw — literal `|` characters under whatever script produced them — so a table emitted there is not a report, it is script output the reader has to parse by eye.

So:

- **Build quietly.** The fetching and formatting run as commands whose visible output is a short confirmation — counts, failures, the widest row — and nothing else. Never dump raw JSON, a draft table, or the finished listing to the screen on the way.
- **Present the finished tables in the reply**, where they render.
- **Never do both.** Emitting the full listing as command output *and* restating it in the reply prints the whole report twice, and a long doubled report is where width damage becomes impossible to spot.

The failure mode in each direction is worth naming, because both have happened: printing it twice buries the reader in duplication; printing it *only* as command output hands them an unrendered wall of pipes. The report goes in the reply, once.

Below everything, if any issue's prefix disagreed with its GitHub state, list them under **Inconsistencies** with repo, number and both values. Don't fix them here beyond the missing-prefix repair, and don't count them twice — just surface them, and point at `/wow-addon:issue-triage`.

Close with one line: how many issues shown, across how many repos, and — when the default states are in play — how many are `untriaged`, since that is the number that means work nobody has decided on.

## Hard rules

- **Read-only, with exactly one exception:** repairing a missing title prefix. Never create, never close, never reopen, never comment, never edit a body or a title's text.
- **Announce every repair.** Silent mutation from a listing command is how trust in a tool dies.
- **Never report an unreadable repo as empty.**
- **Never invent a description.** `—` is a fine answer; a plausible-sounding paraphrase is not.
- **Never mangle the URL.** Bare, complete, one per row, last column. No markdown wrapper, no shortener, no ellipsis — a URL a terminal cannot click is a URL that failed at its only job.
- **Never let tool output be the report.** Markdown does not render there. Build quietly, present the tables in the reply, and never do both.
- **Never let a row exceed ~170 characters** (Title ≤ 40, Description ≤ 36 at the current roster). A clipped row can end up rendered under the wrong repo heading, which makes the table actively misleading rather than merely ugly. Truncate the Description; never the URL.
- **Always escape `|` inside a cell** as `\|`, or the row gains phantom columns.
- **Don't infer status from labels.** The title prefix is the data; a label named `triaged` is not.
- **Never use `gh api graphql`.**
- **Don't invent the roster.** Read it from `ADDONS.md` or say plainly that you inferred it.

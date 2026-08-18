---
description: List the addon's GitHub issues grouped by status, ordered most severe first, with a one-line description of each. Defaults to what is still live — `state:untriaged` and `state:triaged`. Pass states to widen it (`done`, `will-not-do`, `all`), a severity to narrow it (`critical`, `high`, `medium`, `low`), and a scope to change repo. The detail view to `/wow-addon:issue-summary`'s counts.
argument-hint: [here|all|<repo>] [untriaged|triaged|done|will-not-do|open|closed|all] [critical|high|medium|low]
allowed-tools: [Bash, Read]
---

Show what is actually in the issue store, item by item, with enough of each to recognise it without opening GitHub.

This is the companion to `/wow-addon:issue-summary`: that one answers *how much and how bad*, this one answers *what*. Where summary prints grids of counts across repos, this prints the issues themselves.

## Step 0 — Preflight

`gh auth status` — if `gh` is missing or unauthenticated, say so, tell the user to run `gh auth login`, and stop.

**GitHub API guardrail.** Use `gh issue list` with `--json`. **Never use `gh api graphql`** or a hand-rolled query against `api.github.com/graphql`. Status and severity live in **labels**, so filtering by either is a `--label` query or a filter over the `labels` array — not a title filter and not a search.

## Step 1 — Resolve the scope

The **first** `$ARGUMENTS` token, if it is a scope keyword:

- **absent, or `here`** → the repo at the cwd. **This is the default.**
- **`all`** → every addon repo plus the three upstreams (`WowAddonStandards`, `LibKa0s`, `wow-addon`). Read the addon roster from `WowAddonStandards/standards/ADDONS.md`; if unreachable, fall back to sibling directories with a `.toc` and **say the roster was inferred** — an inferred roster can silently omit a repo, and a missing repo reads as "nothing here" rather than "not checked".
- **a repo name** → that repo alone, matched case-insensitively against the roster. No match → say so, list the valid names, and stop. Don't guess at a near-miss.

If the cwd is not a repo `gh` can resolve and no scope was given, **ask** which scope to use rather than guessing.

## Step 2 — Resolve the states and the severity filter

The remaining token(s) select which statuses and which severities to show. Accept them comma- or space-separated, in either order.

**States:**

- **absent** → **`untriaged` + `triaged`**. This is the default and it is deliberate: those two are the live store — everything still awaiting a decision or awaiting the work. The terminal states are history, and printing 150 closed issues by default would bury the 20 that need you.
- **`open`** → same as the default (`untriaged` + `triaged`)
- **`closed`** → `done` + `will-not-do`
- **`all`** → all four
- **any of `untriaged`, `triaged`, `done`, `will-not-do`** → exactly those, in any combination

**Severity:**

- **absent** → every severity, including issues with no `severity:` label.
- **any of `critical`, `high`, `medium`, `low`** → only those, in any combination. `critical high` is the useful one and is worth suggesting when a scope returns more rows than fit.

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

Take each issue's **status** from its `state:` label and its **severity** from its `severity:` label. Both are labels; neither is ever read out of the title. A **legacy `[status]` title prefix** is leftover text from the retired prefix scheme — strip it from the *displayed* title so the column stays readable, and if it disagrees with the label, the **label wins** and the disagreement goes in *Inconsistencies*.

**An issue with no `state:` label is repaired on sight**, because every issue in this store always carries one: `gh issue edit <n> --add-label "state:untriaged"` for an open issue, or the matching terminal label for a closed one. This is the **only** write this command makes. State it in the output every time it happens — a read command that silently changes something is worse than one that doesn't repair at all. If the repair fails, show the issue as `untriaged` anyway and say the label could not be added.

**An issue with no `severity:` label is shown with `—` and is not repaired.** Assigning a severity is a judgment call, and this command's job is to show you the store, not to grade it. `/wow-addon:issue-audit` assigns one on sight; say how many rows are unsized and point there.

For each issue produce a **one-line description**: the single most useful sentence about what it is. Take it from the body — the `Evidence` block, the `Severity rationale`, the first line of `Rationale`, or the first substantive sentence — and compress to the Step 5 width budget (≤ 38 characters at the current roster — see *Row width* below, and recompute if the roster changes). **Never invent it**; if the body has nothing usable, write `—` rather than restating the title back in different words. A description that just paraphrases the title is noise pretending to be information.

## Step 5 — Print

Per repo, in roster order, one section each — and **within a repo, one sub-section per status**:

### <Repo> — N issues (<states shown>)

`critical 1 · high 3 · medium 6 · low 2 · — 0`

#### untriaged — N

| # | Sev | Title | Description | Age | URL |
|---|---|---|---|---|---|

Then `#### triaged`, `#### done`, `#### will-not-do`, in that order, each with the same columns. **Untriaged first because it is the only status that means *nobody has looked at this*.**

- **Status is a heading, not a column.** Grouping by status buys back the width the severity column costs and reads better besides: a reader scanning for what needs deciding wants a block, not a value repeated down a column. This is why the table shape changed when severity arrived — see *Row width* below, where the arithmetic makes the case.
- **Sev** is the `severity:` label without the prefix (`critical`, `high`, `medium`, `low`), or `—`. **Sort rows by severity, most severe first**, and within a severity by number descending. Severity is the reading order inside a status block for the same reason it is the queue order in `/wow-addon:issue-triage`: it is the only column that says which of these matters.
- The per-repo severity tally goes on one line directly under the repo heading, before the first sub-section. It is the cheapest useful thing on the page and it lets a reader skip a repo without reading a table.
- **Age** is time since it was opened, humanized (`3d`, `2mo`).
- **`State` is a conditional column, not a permanent one.** GitHub's `open`/`closed` is implied by the status for every well-formed issue, so a permanent column spends width on a value the reader can already infer. Add it **only** to a sub-section that actually contains a label/state disagreement. Otherwise the disagreements are reported in the Inconsistencies list below and the column is pure cost.
- **URL** is the issue's full `https://github.com/<owner>/<repo>/issues/<n>`, **last column, one per row**. Write it bare — no markdown link wrapper, no shortening, no `…` truncation — because the point of this column is that a terminal can detect it and make it clickable, and every one of those transformations breaks that.
- A repo with nothing matching gets one line: `**<Repo>** — no issues matching <states>.` Don't print an empty table. Same for an empty status sub-section: omit the sub-section rather than printing its header over nothing.

**The URL goes in the row, not in a list underneath.** A list below the table makes the reader match a number to a link by eye, which is exactly the step the column removes. It also means the row and its link can never drift apart when the table is sorted or filtered.

### Row width is a correctness constraint, not a style preference

A full issue URL runs to **58 characters** for the longest repo name in the collection and cannot be shortened, so everything else is budgeted around it. Do the arithmetic rather than eyeballing it.

**With status as a column** (7 columns, 8 pipes, 14 padding spaces):

```
8 pipes + 14 padding + 2 (number) + 9 ("untriaged") + 8 ("critical") + 5 (age) + 58 (URL)  =  104 fixed
```

**With status as a sub-heading** (6 columns, 7 pipes, 12 padding spaces):

```
7 pipes + 12 padding + 2 (number) + 8 ("critical") + 5 (age) + 58 (URL)  =  92 fixed
```

Twelve characters, and they come out of the two columns that carry the actual information. That is the whole argument for the sub-heading: severity has to be visible per row because it varies per row, and status does not.

| Row budget | Left for Title + Description (status as heading) |
|---|---|
| 140 | 48 — **unusable**, ~24 each |
| 160 | 68 |
| **170** | **78 — the working target** |
| 180 | 88 |

**Target ~170 characters: Title ≤ 40, Description ≤ 38**, truncating with a trailing `…`.

This is not tidiness. A terminal that renders markdown tables as box drawing **mangles rows past its width** — it clips them, and when it does it can lose the association between a row and its header, so a row from one repo appears under another repo's heading with no header line at all. A reader then trusts a table that is silently lying about which repo they are looking at. Measured on a real 72-issue run: rows reached **207 characters**, 61 of 92 exceeded 160, and that run produced exactly that failure.

If something has to give, **compress the Description, never the URL** — a shortened description is still useful, a shortened URL is not a link. If even that is not enough, narrow the scope: fewer repos, fewer states, or a severity filter (`critical high` is usually the one that helps). Do not widen the table.

**Do not set a budget you have not checked.** The 92-character floor moves with the longest repo name in scope, so recompute it rather than copying the numbers above when the roster changes.

**Escape pipes.** Any `|` inside a title or description must be written `\|`, or it splits the row into extra cells and corrupts every column after it.

### The rendered report belongs in the reply, not in tool output

**Markdown only renders in the assistant's reply.** Inside a command-output block it is displayed raw — literal `|` characters under whatever script produced them — so a table emitted there is not a report, it is script output the reader has to parse by eye.

So:

- **Build quietly.** The fetching and formatting run as commands whose visible output is a short confirmation — counts, failures, the widest row — and nothing else. Never dump raw JSON, a draft table, or the finished listing to the screen on the way.
- **Present the finished tables in the reply**, where they render.
- **Never do both.** Emitting the full listing as command output *and* restating it in the reply prints the whole report twice, and a long doubled report is where width damage becomes impossible to spot.

The failure mode in each direction is worth naming, because both have happened: printing it twice buries the reader in duplication; printing it *only* as command output hands them an unrendered wall of pipes. The report goes in the reply, once.

Below everything, if any issue's `state:` label disagreed with its GitHub state, or an issue carried two `state:` labels, or a leftover title prefix disagreed with the label, list them under **Inconsistencies** with repo, number and both values. Don't fix them here beyond the missing-label repair, and don't count them twice — just surface them, and point at `/wow-addon:issue-triage`.

Close with one line: how many issues shown, across how many repos, how many are `untriaged`, and how many of those are `critical` or `high`. The first is work nobody has decided on; the second is the part of it that is serious.

## Hard rules

- **Read-only, with exactly one exception:** adding a missing `state:` label. Never create, never close, never reopen, never comment, never edit a body or a title, and **never assign a severity** — an unsized issue is shown as `—` and pointed at `/wow-addon:issue-audit`.
- **Announce every repair.** Silent mutation from a listing command is how trust in a tool dies.
- **Never report an unreadable repo as empty.**
- **Never invent a description.** `—` is a fine answer; a plausible-sounding paraphrase is not.
- **Never mangle the URL.** Bare, complete, one per row, last column. No markdown wrapper, no shortener, no ellipsis — a URL a terminal cannot click is a URL that failed at its only job.
- **Never let a row exceed ~170 characters** (Title ≤ 40, Description ≤ 38 at the current roster, with status as a sub-heading). A clipped row can end up rendered under the wrong repo heading, which makes the table actively misleading rather than merely ugly. Truncate the Description; never the URL.
- **Always escape `|` inside a cell** as `\|`, or the row gains phantom columns.
- **Never infer status or severity from the title.** The labels are the data; a leftover `[triaged]` prefix is stale text and is stripped from the display, not read.
- **Never let tool output be the report.** Markdown does not render there. Build quietly, present the tables in the reply, and never do both.
- **Never use `gh api graphql`.**
- **Don't invent the roster.** Read it from `ADDONS.md` or say plainly that you inferred it.

---
description: List the GitHub issues on the current addon's repo, via the gh CLI. Optionally filter by status label (state:untriaged / state:triaged / state:done / state:will-not-do), by severity (severity:critical … severity:low), or by any other label, or switch to closed/all. Read-only — never creates, edits, or closes issues.
argument-hint: [untriaged | triaged | done | will-not-do] | [critical | high | medium | low] | [label] | [closed | all]  (optional; default: open)
allowed-tools: [Bash]
---

List the GitHub issues for the repo at the cwd, using the `gh` CLI.

## The status and severity labels

Issues on a Ka0s addon repo are the durable store of pending work — `docs/pending/LEDGER.md` is retired and `/wow-addon:issue-audit` reads and writes this store. Two facts about every issue are carried as **GitHub labels**:

**Status** — exactly one `state:` label per issue:

| Label | Colour | Meaning | Issue state |
|---|---|---|---|
| `state:untriaged` | red `ff0000` | Seen and recorded; nobody has been asked about it yet | open |
| `state:triaged` | yellow `ffff00` | Decided: not now. Still on the books | open |
| `state:done` | green `00ff00` | Implemented. Terminal | closed |
| `state:will-not-do` | blue `0000ff` | Decided it will never be done. Terminal | closed |

**Severity** — exactly one `severity:` label per issue:

| Label | Colour | Meaning |
|---|---|---|
| `severity:critical` | red `110000` | Taint, combat-lockdown breakage, saved-variable corruption or data loss, an error on a common path |
| `severity:high` | orange `110800` | A user-visible defect, or a Ka0s standard deviation carried from an audit bundle |
| `severity:medium` | yellow `111100` | Maintainability: a stub callers depend on, code/doc drift, a dead path |
| `severity:low` | green `001100` | Polish, naming, cosmetic, speculative-future notes |

**The title carries neither.** Titles are the plain statement of the work — no `[status]` prefix, no emoji marker, no severity word. The old `[untriaged] …` title-prefix convention is **retired**; if you meet a stale prefix on an old issue, the labels are the truth and the prefix is leftover text.

**Every issue always carries one `state:` label and one `severity:` label**, so a missing one is a defect rather than a fifth value. This command is a plain listing and deliberately does **not** repair it: show the issue with `—` in that column, say plainly which label is missing, and point at `/wow-addon:issue-audit` or `/wow-addon:issue-triage`, which repair strays on sight. Don't guess, and don't fix it here — a listing that edits what it lists is a surprise nobody asked for.

For status, severity, description and age together rather than a bare listing, use `/wow-addon:issue-details`; for counts across repos, `/wow-addon:issue-summary`.

**GitHub API guardrail.** Use the `gh` CLI subcommands — here that is `gh issue list` and, if a single issue needs expanding, `gh issue view` — with `--json` for structured data. **Never use `gh api graphql`** for issue work, and never hand-roll GraphQL queries against `api.github.com/graphql` — reaching for GraphQL first is a real, observed failure that wastes a round trip on a deprecated path before falling back. If a REST call is genuinely unavoidable, use `gh api repos/{owner}/{repo}/issues` — never the GraphQL endpoint. Because status and severity are labels, filtering by either is a **plain `--label` query** — never a title filter, never `--search`, never GraphQL.

## Step 0 — Preflight

Run, and stop with clear guidance if either fails:

1. `gh auth status` — confirm `gh` is installed and authenticated. If not, tell the user to install `gh` and run `gh auth login`, then stop.
2. `gh repo view --json nameWithOwner` — confirm the cwd repo has a GitHub remote `gh` can resolve. If it can't (no remote, not a GitHub repo), say so and stop.

## Step 1 — Parse the argument

Parse `$ARGUMENTS` (trimmed), in this order:

- Empty → list **open** issues (default).
- `closed` → closed issues. `all` → open + closed.
- One of `untriaged`, `triaged`, `done`, `will-not-do` (bare, or written in full as `state:done`) → a **status filter** on the label `state:<value>`. Fetch with `--state all` so the filter means what it says — `done` and `will-not-do` live in the closed set, so filtering an open-only fetch by them silently returns nothing.
- One of `critical`, `high`, `medium`, `low` (bare, or written in full as `severity:high`) → a **severity filter** on the label `severity:<value>`, over open issues.
- Anything else → a plain **label filter** on open issues (e.g. `bug`, `enhancement`).

A status filter and a severity filter **do** combine — `gh issue list --label` is AND across repeated flags, so `untriaged high` is a legitimate and useful request. A plain label filter combines with them the same way. If the user gives two filters of the *same* kind (two statuses, two severities), honour the first and say the second was ignored; the labels are mutually exclusive, so an AND of two of them always returns nothing.

## Step 2 — Fetch

Fetch as JSON for reliable parsing (do not screen-scrape the plain output):

```
gh issue list --state <state> --limit 100 --json number,title,state,labels,author,createdAt,url [--label "state:<value>"] [--label "severity:<value>"] [--label "<label>"]
```

Repeat `--label` once per filter Step 1 produced. Never translate a label filter into a `--search` or a GraphQL query.

## Step 3 — Report

Print a table sorted by severity (critical first), and within a severity by issue number descending (newest first):

| # | Status | Severity | Title | State | Labels | Author | Age |
|---|--------|----------|-------|-------|--------|--------|-----|

- **Status** = the `state:` label with the prefix dropped (`untriaged`, `triaged`, `done`, `will-not-do`), or `—` when the issue carries none.
- **Severity** = the `severity:` label with the prefix dropped (`critical`, `high`, `medium`, `low`), or `—` when the issue carries none.
- **Labels** = the remaining labels only. `state:` and `severity:` have their own columns, and repeating them there wastes the width the real labels need.
- **State** = `open` / `closed`. Show it whenever the scope can contain both; a `state:triaged` issue that is closed is an inconsistency worth seeing.
- **Age** = how long ago it was opened, humanized (e.g. `3d`, `2mo`).
- Above the table, state the count and scope (e.g. "**7 open issues**", "**3 open issues labeled `bug`**", "**4 `state:triaged` issues**").
- When the scope is broad enough to be worth it, add two one-line tallies under the count: `untriaged 5 · triaged 4 · done 12 · will-not-do 3` and `critical 1 · high 6 · medium 12 · low 5`.
- Below the table, list the issue URLs so they're clickable.
- If there are none, say so plainly (e.g. "No open issues.", "No `state:triaged` issues.").

## Hard rules

- **Read-only.** Never run `gh issue create`, `gh issue close`, `gh issue edit`, `gh issue comment`, `gh label create`, or any mutation. This command only lists. In particular, never "tidy up" a missing `state:` or `severity:` label — report it, leave it.
- **Never use `gh api graphql`** or a hand-rolled GraphQL query. `gh issue list --json` is the whole surface this command needs.
- **Status and severity are labels, not title text.** Never parse a `[status]` prefix out of a title to decide either — a stale prefix on an old issue is leftover text, and trusting it over the label is how a migrated repo reads wrong.
- **Don't paginate silently past 100.** If the repo has more than 100 matching issues, say the list is capped and how to narrow it (by status, by severity, or by label).

---
description: Create a well-formed GitHub issue on the current addon's repo, via the gh CLI. Gathers a title, tag (bug/enhancement), severity and details from you — fuzzy input is fine — formulates a clean issue with the `state:` and `severity:` labels the collection uses, shows it for approval, then creates it.
argument-hint: [rough title / details to seed from]  (optional)
allowed-tools: [Bash]
---

Create a new GitHub issue on the repo at the cwd, using the `gh` CLI. Your inputs can be fuzzy — you formulate a clean, well-structured issue from them.

## The status and severity labels

Issues on a Ka0s addon repo are the durable store of pending work — `docs/pending/LEDGER.md` is retired and `/wow-addon:issue-audit` reads and writes this store. Two facts about every issue are carried as **GitHub labels**:

**Status** — exactly one `state:` label per issue:

| Label | Color | Meaning | Issue state |
|---|---|---|---|
| `state:untriaged` | red `ff0000` | Seen and recorded; nobody has been asked about it yet | open |
| `state:triaged` | yellow `ffff00` | Decided: not now. Still on the books | open |
| `state:done` | green `00ff00` | Implemented. Terminal | closed |
| `state:will-not-do` | blue `0000ff` | Decided it will never be done. Terminal | closed |

**Severity** — exactly one `severity:` label per issue:

| Label | Color | Meaning |
|---|---|---|
| `severity:critical` | red `110000` | Taint, combat-lockdown breakage, saved-variable corruption or data loss, an error on a common path |
| `severity:high` | orange `110800` | A user-visible defect, or a Ka0s standard deviation carried from an audit bundle |
| `severity:medium` | yellow `111100` | Maintainability: a stub callers depend on, code/doc drift, a dead path |
| `severity:low` | green `001100` | Polish, naming, cosmetic, speculative-future notes |

**The title carries neither.** A title is the plain statement of the work — no `[status]` prefix, no emoji marker, no severity word. The old `[untriaged] …` title-prefix convention is **retired**; never reintroduce it, and if the user's rough title arrives carrying one, strip it and set the label instead.

**A newly filed issue is `state:untriaged`.** That is the default and it is almost always right: filing an issue records that something exists, not that a decision was taken about it. The only exception is when the user is **explicitly** filing something they have already decided to postpone — then, and only then, file it as `state:triaged`. Never file `state:done` or `state:will-not-do` here; those are closed states and this command only creates open issues.

Never invent a fifth status or a fifth severity, and never duplicate either into the title or the body — the labels are the data.

**GitHub API guardrail.** Use the `gh` CLI subcommands — `gh issue list`, `gh issue create`, `gh issue edit`, `gh issue close`, `gh issue comment`, `gh issue view`, `gh label list`, `gh label create`. Where structured data is needed, use `--json` on those subcommands. **Never use `gh api graphql`** for issue work, and never hand-roll GraphQL queries against `api.github.com/graphql` — reaching for GraphQL first is a real, observed failure that wastes a round trip on a deprecated path before falling back. If a REST call is genuinely unavoidable, use `gh api repos/{owner}/{repo}/issues` — never the GraphQL endpoint. Because status and severity are labels, listing by either is a plain `--label` query.

## Step 0 — Preflight

Run, and stop with clear guidance if either fails:

1. `gh auth status` — confirm `gh` is installed and authenticated. If not, tell the user to install `gh` and run `gh auth login`, then stop.
2. `gh repo view --json nameWithOwner` — confirm the cwd repo has a GitHub remote `gh` can resolve. If it can't, say so and stop.

## Step 1 — Gather inputs

Collect four things from the user (use `$ARGUMENTS` as a seed if provided — e.g. treat it as the rough title/details and only ask for what's missing):

1. **Title** — a rough one-liner is fine.
2. **Tag** — `bug` or `enhancement`. If unclear, ask; don't guess.
3. **Severity** — `critical`, `high`, `medium` or `low`, per the table above. **Propose one with a one-line justification** drawn from what they described, and let them accept or override it. Don't make them look the ladder up, and don't file without one.
4. **Details** — free-form; whatever the user can describe. May be messy.

Ask for anything missing. Do not proceed to draft until you have all four.

## Step 2 — Formulate the issue

Turn the fuzzy inputs into a clean issue:

- **Title** — crisp and specific; imperative or noun phrase, no trailing period, **no status prefix and no severity word**. Fix obvious typos. (e.g. "aura timer flickers on target swap" → `Aura timer flickers when swapping targets`.) If their rough title arrives carrying a legacy `[untriaged]`-style prefix, strip it — status is the label now.
- **Body** — structure by tag:
  - **bug** → `### Description` · `### Steps to reproduce` · `### Expected` · `### Actual` · `### Environment` (fill in the addon version and `## Interface:` from the TOC if determinable; otherwise leave a clearly-marked blank for the user).
  - **enhancement** → `### Description` · `### Motivation` · `### Proposed behavior` · `### Acceptance criteria`.
- Only include information the user actually gave (plus TOC-derived environment facts). **Do not invent** reproduction steps, versions, or acceptance criteria — where something is unknown, leave a short `_TBD_` placeholder rather than fabricating.
- **Labels** — three of them: the `state:` label (`state:untriaged`, or `state:triaged` in the explicit postponement case), the `severity:` label from Step 1, and the tag label (`bug` or `enhancement`).

### Step 2a — Ensure the label set exists

Before creating, make sure the eight collection labels exist on this repo. `gh label create --force` creates a missing label and updates an existing one's color and description, so it is safe to run every time and it repairs a drifted color on the way:

```
gh label create "state:untriaged"   --color ff0000 --description "Seen and recorded; nobody has been asked yet"  --force
gh label create "state:triaged"     --color ffff00 --description "Decided: not now. Still on the books"          --force
gh label create "state:done"        --color 00ff00 --description "Implemented. Terminal"                          --force
gh label create "state:will-not-do" --color 0000ff --description "Will never be done. Terminal"                   --force
gh label create "severity:critical" --color 110000 --description "Taint, lockdown, data loss, common-path error"  --force
gh label create "severity:high"     --color 110800 --description "User-visible defect, or a standard deviation"   --force
gh label create "severity:medium"   --color 111100 --description "Maintainability: stub, drift, dead path"        --force
gh label create "severity:low"      --color 001100 --description "Polish, naming, cosmetic, speculative"          --force
```

Run only the ones `gh label list` shows as missing or wrong, and space the calls a second or two apart. If a create fails, say so and carry on — a missing label is a reason to report, not to lose the user's issue.

The `bug` / `enhancement` tag labels are GitHub defaults and usually already exist. If the tag label is missing, still create the issue and note that the tag was skipped (or offer to create it).

## Step 3 — Confirm before creating

Show the drafted **title**, **body**, and **all three labels**, then ask:

> "Create this issue? (y / n / edit)"

- **y** → proceed to Step 4.
- **n** → stop without creating anything.
- **edit** → ask what to change, revise, re-show the full draft, and re-ask.

## Step 4 — Create

On approval, create it via a heredoc for the body (preserves Markdown/newlines):

```
gh issue create --title "<title>" \
  --label "state:untriaged" --label "severity:<level>" --label "<tag>" \
  --body "$(cat <<'EOF'
<body>
EOF
)"
```

Omit a `--label` only when that label doesn't exist and the user declined to create it — and say which one was dropped. Print the new issue's URL that `gh` returns.

## Hard rules

- **Only create on explicit approval.** No issue is filed until the user answers `y` in Step 3.
- **Always carry both a `state:` and a `severity:` label**, and default the status to `state:untriaged`. Never file `state:done` or `state:will-not-do` — those are closed states owned by `/wow-addon:issue-triage`.
- **Never put status or severity in the title.** No `[untriaged]` prefix, no emoji marker, no severity word. The labels are the data.
- **Never invent a severity silently.** Propose one with a justification and let the user overrule it; a severity nobody agreed to is worse than asking.
- **Never touch other issues.** This command only creates the one new issue — no editing, closing, or commenting on anything else. The only other write it makes is `gh label create --force` on the eight collection labels.
- **Never use `gh api graphql`** or a hand-rolled GraphQL query for issue work. `gh issue create`, `gh label list` and `gh label create` are the whole surface this command needs; `gh api repos/{owner}/{repo}/issues` is the only acceptable fallback.
- **Don't fabricate.** Reproduction steps, versions, and acceptance criteria come from the user or the TOC, never from imagination — mark unknowns `_TBD_`.

---
description: Create a well-formed GitHub issue on the current addon's repo, via the gh CLI. Gathers a title, tag (bug/enhancement), and details from you — fuzzy input is fine — formulates a clean issue, shows it for approval, then creates it.
argument-hint: [rough title / details to seed from]  (optional)
allowed-tools: [Bash]
---

Create a new GitHub issue on the repo at the cwd, using the `gh` CLI. Your inputs can be fuzzy — you formulate a clean, well-structured issue from them.

## Step 0 — Preflight

Run, and stop with clear guidance if either fails:

1. `gh auth status` — confirm `gh` is installed and authenticated. If not, tell the user to install `gh` and run `gh auth login`, then stop.
2. `gh repo view --json nameWithOwner` — confirm the cwd repo has a GitHub remote `gh` can resolve. If it can't, say so and stop.

## Step 1 — Gather inputs

Collect three things from the user (use `$ARGUMENTS` as a seed if provided — e.g. treat it as the rough title/details and only ask for what's missing):

1. **Title** — a rough one-liner is fine.
2. **Tag** — `bug` or `enhancement`. If unclear, ask; don't guess.
3. **Details** — free-form; whatever the user can describe. May be messy.

Ask for anything missing. Do not proceed to draft until you have all three.

## Step 2 — Formulate the issue

Turn the fuzzy inputs into a clean issue:

- **Title** — crisp and specific; imperative or noun phrase, no trailing period. Fix obvious typos. (e.g. "aura timer flickers on target swap" → `Aura timer flickers when swapping targets`.)
- **Body** — structure by tag:
  - **bug** → `### Description` · `### Steps to reproduce` · `### Expected` · `### Actual` · `### Environment` (fill in the addon version and `## Interface:` from the TOC if determinable; otherwise leave a clearly-marked blank for the user).
  - **enhancement** → `### Description` · `### Motivation` · `### Proposed behavior` · `### Acceptance criteria`.
- Only include information the user actually gave (plus TOC-derived environment facts). **Do not invent** reproduction steps, versions, or acceptance criteria — where something is unknown, leave a short `_TBD_` placeholder rather than fabricating.
- **Label** — map the tag to the GitHub label `bug` or `enhancement`. Check it exists with `gh label list`; if the label is missing, still create the issue and note that the label was skipped (or offer to create it).

## Step 3 — Confirm before creating

Show the drafted **title**, **body**, and **label**, then ask:

> "Create this issue? (y / n / edit)"

- **y** → proceed to Step 4.
- **n** → stop without creating anything.
- **edit** → ask what to change, revise, re-show the full draft, and re-ask.

## Step 4 — Create

On approval, create it via a heredoc for the body (preserves Markdown/newlines):

```
gh issue create --title "<title>" --label "<label>" --body "$(cat <<'EOF'
<body>
EOF
)"
```

Omit `--label` if the label doesn't exist and the user declined to create it. Print the new issue's URL that `gh` returns.

## Hard rules

- **Only create on explicit approval.** No issue is filed until the user answers `y` in Step 3.
- **Never touch other issues.** This command only creates the one new issue — no editing, closing, or commenting on anything else.
- **Don't fabricate.** Reproduction steps, versions, and acceptance criteria come from the user or the TOC, never from imagination — mark unknowns `_TBD_`.

---
description: Stage and commit all changes in the current addon's git repo with a generated commit message. Commits without asking by default; pass "ask" as the argument to require approval first.
argument-hint: [commit message]  |  ["ask" to require approval]
allowed-tools: [Bash, Read, Glob, Grep]
---

Commit all changes in the addon at the cwd.

## Argument modes

Parse `$ARGUMENTS` (after `trim().toLowerCase()`):

- **Approval mode**: `$ARGUMENTS` matches one of `ask`, `ask for approval`, `ask for my approval`, `approve`, `--ask`, `-a`, `interactive`, `confirm`. Auto-generate the commit message and **ask the user to confirm** before committing.
- **Custom-message mode**: `$ARGUMENTS` is non-empty and doesn't match the approval phrases above. Use `$ARGUMENTS` verbatim as the commit message. Commit without asking.
- **Default mode**: `$ARGUMENTS` is empty. Auto-generate the commit message. Commit without asking.

In all three modes, the safety prompts in Step 2 (unusual untracked files, secret-looking filenames) still pause for the user — auto mode is not a license to commit anything.

## Step 1 — Detect git and changes

1. Run `git rev-parse --is-inside-work-tree`. If not a git repo, tell the user and stop.
2. In parallel:
   - `git status --short`
   - `git diff` (unstaged tracked changes)
   - `git diff --cached` (already-staged changes)
   - `git log -5 --format='%h %s'` (to match the project's commit message style)
3. If working tree is clean and nothing is staged, tell the user "Nothing to commit." and stop.

## Step 2 — Decide what to stage

- In **custom-message mode**, the commit message is `$ARGUMENTS` verbatim.
- In **default** and **approval** modes, generate a commit message based on the actual diff. Match the style of the recent commits (terse vs. detailed, conventional-commits prefix or not, present tense vs past, etc.). The message should describe **why**, not just **what** — what user-visible behavior changed. One-line subject (≤72 chars), optionally followed by a body if the change is non-trivial.
- **Untracked files**: list them. **Always ask** the user before adding any that look unusual (anything outside the addon's normal file types: `.bak`, `.lua.swp`, IDE files, `.env`, `secrets.*`, `*.pem`, `*.key`, `*credentials*`, `*token*`, dump files, large binaries the addon doesn't ship, etc.). Skip those if the user says no. This safety check applies in all modes including default/auto.

## Step 3 — Print the plan

Always print, regardless of mode:
- Files to be staged (one per line)
- The commit message you're about to use (full subject + body)
- The mode you're operating in (`auto`, `custom-message`, or `approval`) so the user can see what's happening

Then:

- In **approval mode**, ask: "Commit with this message? (y / n / edit)"
  - **y**: proceed to Step 4
  - **n**: stop without committing
  - **edit**: ask the user for a new message, re-print the plan with the new message, re-ask
- In **default** and **custom-message** modes, proceed directly to Step 4. (The Step 2 safety prompt for unusual untracked files has already gated anything risky.)

## Step 4 — Commit

1. `git add <each file>` (named files only — never `git add -A` or `git add .` to avoid catching anything sensitive)
2. `git commit -m "$(cat <<'EOF' ... EOF)"` using a heredoc for proper formatting
3. Run `git status` after to confirm the commit landed and the tree is clean

## Step 5 — Report

Print:
- The new commit hash and subject
- A reminder to push if the user wants the change on a remote — but **do not push**.

## Hard rules

- **Never `--no-verify`, `--no-gpg-sign`, or `--amend`** unless the user explicitly asks.
- **Never push.** The user pushes when they're ready.
- **Never `git add -A` / `git add .`** — always name files.
- **Never commit files that look like secrets** (`.env`, `*.pem`, `*credentials*`, `*token*`, `*.key`). Warn and ask before staging any of these — applies in every mode including auto.
- If a pre-commit hook fails, fix the underlying issue and create a new commit (do not amend).

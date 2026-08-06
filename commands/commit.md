---
description: Stage and commit all changes in the current addon's git repo with a generated commit message. Commits without asking by default; pass "ask" to require approval first, and "push" to push the branch afterwards. Does not push unless asked.
argument-hint: [commit message] | ["ask" to require approval] | ["push" to push after committing] | ["push <message>"]
allowed-tools: [Bash, Read, Glob, Grep]
---

Commit all changes in the addon at the cwd.

## Argument modes

Two independent things are being chosen: **how the message is decided**, and **whether to push afterwards**.

**Message mode** — parse `$ARGUMENTS` (after `trim().toLowerCase()`):

- **Approval mode**: matches one of `ask`, `ask for approval`, `ask for my approval`, `approve`, `--ask`, `-a`, `interactive`, `confirm`. Auto-generate the message and **ask the user to confirm** before committing.
- **Custom-message mode**: non-empty and not an approval phrase. Use it **verbatim** as the commit message. Commit without asking.
- **Default mode**: empty. Auto-generate the message. Commit without asking.

**Push flag** — `push`, `--push`, `-p`, `and push`, `push it`. **Default is not to push.**

### Parsing the two together, without eating the message

The flag has to combine with everything else while never swallowing a word from a custom message. So:

1. Split `$ARGUMENTS` on whitespace.
2. If **every** token is a recognised flag (approval and/or push), it is flag-only: no custom message.
3. Otherwise there is a custom message. Consume a push flag **only if it is the leading token**; everything after it is the message, verbatim.

| Argument | Message | Push |
|---|---|---|
| *(empty)* | auto-generated | no |
| `ask` | auto-generated, confirmed | no |
| `push` | auto-generated | **yes** |
| `ask push` / `push ask` | auto-generated, confirmed | **yes** |
| `Fix the border flicker` | verbatim | no |
| `push Fix the border flicker` | `Fix the border flicker` | **yes** |
| `Refactor the slash push handler` | verbatim, **all of it** | no |

That last row is the reason the flag is only consumed at the **start**. A trailing or embedded `push` belongs to the message — silently dropping a word from someone's commit message, or pushing because their message happened to end in "push", are both worse than making them put the flag first.

In every mode, the safety prompts in Step 2 (unusual untracked files, secret-looking filenames) still pause for the user — auto mode is not a license to commit anything, and the push flag is not a license to skip them.

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
- **Whether it will push**, and if so to which remote and branch. State this even when the answer is no — "will not push" is the default and the reader should be able to confirm it at a glance rather than infer it from silence.

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

## Step 5 — Push, only if asked

Skip this entirely unless the push flag was given. **The default is not to push.**

If it was:

1. **Only push a commit that actually landed.** If Step 4 failed — a hook rejected it, nothing was staged — do not push. There is nothing to push, and pushing whatever the branch already had is not what was asked for.
2. `git rev-parse --abbrev-ref HEAD` for the branch, and `git rev-parse --abbrev-ref @{u}` for its upstream.
3. **Upstream exists** → `git push`. Report the remote, the branch and the commit range that moved.
4. **No upstream** → say so and **ask** before running `git push -u origin <branch>`. Setting an upstream creates a branch on the remote and binds this one to it; that is a different act from pushing to a branch that already exists, and the flag asked for the second.
5. **Push rejected** (non-fast-forward, protected branch, auth) → report the failure verbatim and **stop**. Do not pull, do not rebase, do not merge, and never `--force` or `--force-with-lease`. Reconciling diverged history is a decision with a wrong answer that loses work; it belongs to the user, not to a commit command.

The commit is already safe on disk at this point, so a failed push costs nothing but a message.

## Step 6 — Report

Print:
- The new commit hash and subject
- **If pushed**: the remote and branch it went to, and confirmation the push succeeded
- **If not pushed**: say so plainly, and mention that `push` as an argument would have done it — one line, not a lecture

## Hard rules

- **Never `--no-verify`, `--no-gpg-sign`, or `--amend`** unless the user explicitly asks.
- **Never push unless the push flag was given.** The default is no push, and an auto-generated message is not a reason to assume otherwise. When it was given: push the current branch only, never `--force` or `--force-with-lease`, never push a commit that did not land, and never resolve a rejected push by pulling, rebasing or merging — report it and stop.
- **Never `git add -A` / `git add .`** — always name files.
- **Never commit files that look like secrets** (`.env`, `*.pem`, `*credentials*`, `*token*`, `*.key`). Warn and ask before staging any of these — applies in every mode including auto.
- If a pre-commit hook fails, fix the underlying issue and create a new commit (do not amend).

---
description: Finish a changeset that spans several sibling repos — sync docs, commit, merge any feature branch to master, push, and delete the branch, in each repo, in dependency order. Detects which repos changed; a vendored shared library is always finalized before its consumers.
argument-hint: [repo names or paths, space-separated]  |  omit to auto-detect changed siblings
allowed-tools: [Bash, Read, Glob, Grep, Edit, Write, Task, Skill]
---

Finish a piece of work that touched **more than one repository** — the case a per-repo commit command cannot handle, because the repos have to land in the right order and each one still needs its own docs synced and its own gate run.

Per repo, in this order: `/wow-addon:sync-docs` → `/wow-addon:commit` → merge any feature branch to `master` → push to origin → delete the branch. Repos that depend on another repo wait for it.

`$ARGUMENTS` names the repos to finalize (names relative to the parent directory, or paths). Omit it and the scope is auto-detected — see Step 1.

## Step 1 — Establish the scope

The unit of work is a **changeset**: the repos that were changed together, for one reason, in this session.

1. From the cwd repo, take the parent directory as the collection root. List every sibling that is a git repo (`ls -d ../*/.git`).
2. For each, run `git -C <repo> status --porcelain` and `git -C <repo> log --oneline origin/HEAD..HEAD 2>/dev/null`. A repo is **in scope** if it has uncommitted changes **or** unpushed commits.
3. If `$ARGUMENTS` is non-empty, use exactly those repos instead — but still run the status check on each and say so if one is already clean, rather than pretending you finalized it.

Print the scope as a list before doing anything, and **stop if it is empty** ("Nothing to finalize.").

**A repo with a dirty tree you did not expect is a stop, not a step.** If a repo in scope holds changes that are obviously not part of this changeset — an unrelated feature half-written, a stash-shaped mess, files you cannot account for from the session's own work — name them and ask before proceeding. Committing someone else's work-in-progress under your changeset's message is not recoverable by a revert, because the message is now wrong for both.

## Step 2 — Derive the dependency chain

Order is not cosmetic. Get it wrong and a repo lands on origin citing a path or a version that does not exist there yet.

Establish, with evidence rather than assumption:

- **Vendored shared libraries.** If repo B carries `libs/<Lib>/` (or `tests/_kit/`) whose source is repo A in the same collection, then **A precedes B**. Confirm the relationship — `diff -r --strip-trailing-cr A/<Lib> B/libs/<Lib>` — rather than inferring it from the name.
- **Cross-repo references in the changed files themselves.** `grep` the diff for sibling paths (`../<Repo>/…`). A ledger row or doc line in B that cites a file in A is a dependency: A must be committed and pushed first, or B's reference points at nothing on origin.
- **Release order.** If the changeset includes a version tag in A that B's docs or provenance line name, A goes first.

Repos with **no** dependency on each other are independent and should be finalized **in parallel**. Print the chain you derived — e.g. `LibKa0s → (AbsorbTracker | BankLedger | ConsumableMaster | KickCD)` — and the evidence for each edge, before executing.

## Step 3 — Execute, per repo

Run the stages below **in the repo's own root**. When several repos are independent, run them concurrently — one `Task` per repo, or a workflow if the user has opted into multi-agent orchestration — but never let two agents touch the same repo, and never start a dependent repo before its dependency has **pushed**.

### 3a. Sync the docs

Run `/wow-addon:sync-docs` for that repo. Two bindings that matter here more than in a single-repo run:

- **Content sync only.** That command asks the user to confirm before scaffolding or restructuring a missing `docs/ARCHITECTURE.md` or `CLAUDE.md`/`docs/agent-context.md` pair. In a multi-repo run — especially a parallel one — nobody is there to answer per repo. Do not create or move documents; record what you would have proposed and surface it in the final report.
- **A repo in the collection may not be an addon.** A shared library has no `.toc`, no slash commands, no schema. Skip the TOC-derived steps and apply the rest: does the README still describe what it ships, do the counts hold, is the version claim true.

### 3b. Re-run that repo's gate

Docs edits are not supposed to move a gate, which is exactly why running it is cheap and the omission is expensive — a doc sync that regenerates a test-case inventory can disagree with the suite that produced it.

```
lua tests/run.lua        # or whatever /wow-addon:run-tests discovers
luacheck .
```

Plus, in any repo that vendors a shared library, the vendor-drift gate — both readings:

```
diff -r --strip-trailing-cr ../<Lib>/<Lib> libs/<Lib>   # content — MUST be empty
diff -r ../<Lib>/<Lib> libs/<Lib>                       # bytes  — SHOULD be empty
```

**A red gate stops that repo.** Do not commit it, do not push it, and do not start anything that depends on it. Finish the other repos, then report the failure with its real output.

### 3c. Commit

Run `/wow-addon:commit` for that repo, in its default (auto) mode, and honour everything that command already says: named files only, never `git add -A`, never `--amend`, never `--no-verify`, match the repo's own commit-message style, and pause for anything secret-shaped.

One addition for the multi-repo case: **one commit per repo, and the message is written for that repo's reader.** The same changeset looks different from each side — the library's commit is about what it published, the consumer's is about what it now carries and what changed for its users. A message that only makes sense if you have read the other four repos' commits is the wrong message.

### 3d. Merge the branch, if there is one

`git branch --show-current`. If it is already `master` (or the repo's default), the merge and delete stages are **no-ops — say so explicitly in the report** rather than skipping them silently. A reader cannot tell "there was no branch" from "the step was forgotten" unless you write it down.

If there is a feature branch:

1. `git checkout master && git pull --ff-only origin master` — a diverged master is a stop, not something to force.
2. `git merge --no-ff <branch>` — `--no-ff` so the branch's shape survives in history.
3. Conflicts are a **stop**. Do not resolve a conflict you did not anticipate as part of a bulk finalize; report it and leave the repo mid-merge for the user, naming the conflicted paths.
4. Re-run the gate on the merge result. A merge that compiles is not a merge that passes.

### 3e. Push

`git push origin master`. This command **does** push — that is the point of it, and it is the one place it deliberately overrides `/wow-addon:commit`'s "never push" rule. Paste the real output; a push that says `Everything up-to-date` when you expected a new ref is a finding.

If the push is rejected (someone else moved origin), stop that repo: pull, re-run the gate, and report. Never `--force`.

### 3f. Delete the branch

Only after the push, and only if 3d actually merged something:

```
git branch -d <branch>              # -d, never -D: it refuses if the work is not merged
git push origin --delete <branch>
```

`-d` failing is information, not an obstacle to route around. If it refuses, something is unmerged — report it and leave the branch alone.

## Step 4 — Report

One table, one row per repo:

| Repo | Docs synced | Gate | Commit | Branch | Pushed |
|---|---|---|---|---|---|
| LibKa0s | 2 files | 407 pass, 0/0 | `a1b2c3d` | master (no branch — merge/delete n/a) | ✅ |

Then, below it:

- **What was deliberately not done** — every restructuring 3a declined to make, per repo, so the user can decide.
- **Dead exports** surfaced by the doc sync (never deleted).
- **Anything that stopped** — a red gate, a conflict, a rejected push — with the real output and what state that repo is in now.
- The dependency chain you executed, so the ordering is auditable after the fact.

Be exact about partial success. "Four of five repos are pushed; ConsumableMaster stopped on a red gate and is committed but unpushed" is useful. "Done" is not.

## Hard rules

- **Never `git add -A` / `git add .`** — named files only, in every repo.
- **Never `--force`, `--amend`, `--no-verify`, or `git branch -D`.** Each of them turns a stop into silent data loss.
- **Never commit a repo whose gate is red**, and never push one, even if the failure looks unrelated to the changeset.
- **Never start a dependent repo before its dependency has pushed.** The whole reason for Step 2.
- **Never edit a vendored folder** (`libs/`, `tests/_kit/`) to make anything pass. A defect there is an upstream finding: fix it in the library repo, bump the file's LibStub minor, re-vendor as its own commit. A local patch is reverted silently by the next copy.
- **Do not bump versions or write CHANGELOG entries.** That is `/wow-addon:bump-version`'s job, and a changeset's CHANGELOG entry is usually already written by the work itself.
- **Do not tag.** If the changeset needs a release tag, that is a separate, deliberate act.
- **One repo, one agent.** Concurrency is per repo; two agents in one working tree will interleave `git add` and stage each other's files.

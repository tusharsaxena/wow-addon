---
description: Finish a changeset — sync docs, commit, merge any feature branch to master, push, and delete the branch. Works on the current repo alone or on several sibling repos in dependency order; establishes which by evidence and asks when the scope is not certain.
argument-hint: [repo names or paths, space-separated | "here" for this repo only]  |  omit to establish scope
allowed-tools: [Bash, Read, Glob, Grep, Edit, Write, Task, Skill]
---

Finish a piece of work: get it synced, gated, committed, merged and **pushed**. The changeset may live in one repo or span several sibling repos — this command handles both, and the first thing it does is establish which.

Per repo, in this order: `/wow-addon:sync-docs` → gate → `/wow-addon:commit` → merge any feature branch to `master` → push to origin → delete the branch. When more than one repo is in scope, repos that depend on another repo wait for it.

`$ARGUMENTS` is optional. It may name the repos to finalize (names relative to the parent directory, or paths), or be `here` to mean the current repo and nothing else. Omit it and the scope is established in Step 1.

## Step 1 — Establish the scope

The unit of work is a **changeset**: the repos that were changed together, for one reason. Getting this wrong in either direction is expensive — too narrow and half the changeset sits unpushed while the other half references it on origin; too wide and unrelated work-in-progress gets committed under a message that is now wrong for both.

**Never guess the scope.**

1. If `$ARGUMENTS` is `here` (or names exactly the cwd repo), the scope is this repo alone. Skip to Step 2.
2. If `$ARGUMENTS` names repos, use exactly those — but still run the status check on each and say so if one is already clean, rather than pretending you finalized it. Skip to Step 2.
3. Otherwise, survey. From the cwd repo, take the parent directory as the collection root and list every sibling that is a git repo (`ls -d ../*/.git`). For each, plus the cwd repo, run `git -C <repo> status --porcelain` and `git -C <repo> log --oneline origin/HEAD..HEAD 2>/dev/null`. A repo is a **candidate** if it has uncommitted changes **or** unpushed commits.

Then decide, and only proceed without asking when the answer is certain:

- **No candidates** → stop: "Nothing to finalize."
- **Exactly one candidate** → that is the scope. Say which repo and continue.
- **Several candidates, conclusively one changeset** → the scope is all of them. "Conclusively" means hard evidence, not a hunch: this session's own work touched each of them; or a vendored library in one is a byte-for-byte match for the changed source in another; or a changed file in one cites a sibling path (`../<Repo>/…`) that changed in this same set. Print the evidence per repo, then continue.
- **Anything else** → **ask.** This includes: candidates whose changes look unrelated to each other, candidates you did not touch this session, or any repo holding changes you cannot account for (an unrelated feature half-written, a stash-shaped mess). Do not resolve it by picking the likely answer.

To ask, print one block per candidate — repo name, branch, unpushed commit subjects, and the changed files with a one-line reading of what the change is — then ask which repos are in scope for this finalize. Offer the obvious groupings (all of them / just the cwd repo / a named subset) rather than an open-ended question. Wait for the answer; do not start Step 2 on a provisional scope.

Print the final scope as a list before doing anything.

## Step 2 — Derive the dependency chain

**Single repo in scope?** There is nothing to order. Note it ("single-repo changeset — no dependency chain") and go to Step 3.

With more than one repo, order is not cosmetic. Get it wrong and a repo lands on origin citing a path or a version that does not exist there yet.

Establish, with evidence rather than assumption:

- **Vendored shared libraries.** If repo B carries `libs/<Lib>/` (or `tests/_kit/`) whose source is repo A in the same collection, then **A precedes B**. Confirm the relationship — `diff -r --strip-trailing-cr A/<Lib> B/libs/<Lib>` — rather than inferring it from the name.
- **Cross-repo references in the changed files themselves.** `grep` the diff for sibling paths (`../<Repo>/…`). A ledger row or doc line in B that cites a file in A is a dependency: A must be committed and pushed first, or B's reference points at nothing on origin.
- **Release order.** If the changeset includes a version tag in A that B's docs or provenance line name, A goes first. For `LibKa0s` that provenance line is in B's **root `CLAUDE.md`** — `Bundles [LibKa0s](…) vX.Y.Z (MIT).` — not its `README.md`, since LibKa0s v1.8.1 / test-kit revision 9; grep `CLAUDE.md` for it, and treat a copy still sitting in `README.md` as a defect to report rather than a second source to read.

Repos with **no** dependency on each other are independent and should be finalized **in parallel**. Print the chain you derived — e.g. `LibKa0s → (AbsorbTracker | BankLedger | ConsumableMaster | KickCD)` — and the evidence for each edge, before executing.

## Step 3 — Execute, per repo

Run the stages below **in the repo's own root**. When several repos are independent, run them concurrently — one `Task` per repo, or a workflow if the user has opted into multi-agent orchestration — but never let two agents touch the same repo, and never start a dependent repo before its dependency has **pushed**. With a single repo in scope, run the stages inline; there is nothing to fan out.

### 3a. Sync the docs

Run `/wow-addon:sync-docs` for that repo. Two bindings that matter when the scope is more than one repo:

- **Content sync only.** That command asks the user to confirm before scaffolding or restructuring a missing `docs/ARCHITECTURE.md` or root `CLAUDE.md` stub. In a multi-repo run — especially a parallel one — nobody is there to answer per repo. Do not create or move documents; record what you would have proposed and surface it in the final report. In a **single-repo** run the user is right there: ask, as that command normally would.
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

**The complexity record is not part of *this* gate.** (The **release** gate is all four suites plus zero CCN > 15, and it lives in `/wow-addon:bump-version`, which refuses to bump when any of them fails — `automated-tests-§3`. This command neither evaluates nor re-evaluates it.) Do not run `lizard` here and do not let the complexity record block a commit: its checkpoint is **release, not commit** (`performance-§10`), and a complexity gate on commits is the fastest way to teach a collection to reach for `--no-verify`. There is one thing to *check*, without regenerating anything: if this changeset bumps the version — a new `## Version:` in the TOC, or a fresh `## Version History` row — then it is a release change, and the release change is where the report is refreshed. If no fresh `docs/automated-tests/<run>/` bundle is present in it, say so in the Step 4 report and name `/wow-addon:bump-version` as the command that owns the refresh. Do not regenerate it yourself, do not hold the push for it, and never hand-edit it.

### 3c. Commit

Run `/wow-addon:commit` for that repo, in its default (auto) mode, and honour everything that command already says: named files only, never `git add -A`, never `--amend`, never `--no-verify`, match the repo's own commit-message style, and pause for anything secret-shaped.

One addition when the scope spans repos: **one commit per repo, and the message is written for that repo's reader.** The same changeset looks different from each side — the library's commit is about what it published, the consumer's is about what it now carries and what changed for its users. A message that only makes sense if you have read the other four repos' commits is the wrong message.

### 3d. Merge the branch, if there is one

`git branch --show-current`. If it is already `master` (or the repo's default), the merge and delete stages are **no-ops — say so explicitly in the report** rather than skipping them silently. A reader cannot tell "there was no branch" from "the step was forgotten" unless you write it down.

If there is a feature branch:

1. `git checkout master && git pull --ff-only origin master` — a diverged master is a stop, not something to force.
2. `git merge --no-ff <branch>` — `--no-ff` so the branch's shape survives in history.
3. Conflicts are a **stop**. Do not resolve a conflict you did not anticipate as part of a finalize; report it and leave the repo mid-merge for the user, naming the conflicted paths.
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

One table, one row per repo — even when there is only one:

| Repo | Docs synced | Gate | Commit | Branch | Pushed |
|---|---|---|---|---|---|
| LibKa0s | 2 files | 407 pass, 0/0 | `a1b2c3d` | master (no branch — merge/delete n/a) | ✅ |

Then, below it:

- **What was deliberately not done** — every restructuring 3a declined to make, per repo, so the user can decide.
- **Dead exports** surfaced by the doc sync (never deleted).
- **Anything that stopped** — a red gate, a conflict, a rejected push — with the real output and what state that repo is in now.
- The scope you finalized and, when it was more than one repo, the dependency chain you executed — so the ordering is auditable after the fact.

Be exact about partial success. "Four of five repos are pushed; ConsumableMaster stopped on a red gate and is committed but unpushed" is useful. "Done" is not.

## Hard rules

- **Never guess the scope.** When the candidates are not conclusively one changeset, present them and ask. A wrong scope is not fixable by a revert.
- **Never `git add -A` / `git add .`** — named files only, in every repo.
- **Never `--force`, `--amend`, `--no-verify`, or `git branch -D`.** Each of them turns a stop into silent data loss.
- **Never commit a repo whose gate is red**, and never push one, even if the failure looks unrelated to the changeset.
- **Never start a dependent repo before its dependency has pushed.** The whole reason for Step 2.
- **Never edit a vendored folder** (`libs/`, `tests/_kit/`) to make anything pass. A defect there is an upstream finding: fix it in the library repo, bump the file's LibStub minor, re-vendor as its own commit. A local patch is reverted silently by the next copy.
- **Do not bump versions or write CHANGELOG entries.** That is `/wow-addon:bump-version`'s job, and a changeset's CHANGELOG entry is usually already written by the work itself.
- **Never gate a commit on the complexity record, and never regenerate it here.** Report a release changeset that produced no fresh automated-test bundle; that is the whole of this command's involvement.
- **Do not tag.** If the changeset needs a release tag, that is a separate, deliberate act.
- **One repo, one agent.** Concurrency is per repo; two agents in one working tree will interleave `git add` and stage each other's files.

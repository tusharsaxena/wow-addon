---
description: Sweep the addon for everything still hanging — TODO/FIXME markers, unexecuted audit and review plan items, doc open questions, stale CHANGELOG entries, open GitHub issues, and recorded-but-unacted Claude memory — then bucketize by type and severity, interview you one item at a time (every item can be deferred or closed as "will not do"), and implement what you accept. Records decisions in docs/pending/LEDGER.md so deferrals stay quiet and closed items never come back.
argument-hint: [code|docs|issues|memory|<path>]
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion]
---

Find every pending decision, unfinished action, and deferred change in the WoW addon at the cwd; bring each one to the user for a call; implement the calls they make.

`$ARGUMENTS` optionally narrows the sweep to a single source (`code`, `docs`, `issues`, `memory`) or to a path prefix (only items located under that path). Empty means sweep everything.

## Step 0 — Locate the addon

Confirm the cwd is a WoW addon: at least one `.toc` file, or a `docs/`+`.lua` layout. If it isn't, say so and stop — this command works on an addon repo, not on an arbitrary directory.

Read the newest `docs/pending/LEDGER.md` if one exists. It is the record of past decisions; you need it in Step 2 to avoid re-interviewing settled items.

Note the current git branch (`git rev-parse --abbrev-ref HEAD`) — Step 3.5 needs it.

## Step 1 — Discover

Run all four sweeps (or the one `$ARGUMENTS` selected). Every item you surface must carry:

- a **stable ID** — `<SRC>-<NN>`, where `SRC` is `CODE`, `DOC`, `PLAN`, `GIT`, `ISS`, or `MEM` (e.g. `CODE-03`, `PLAN-01`)
- a **location** — `file:line`, an issue number, or a memory filename
- **verbatim evidence** — the marker comment, the plan row, the issue title. Quote it; don't paraphrase.
- an **evidence hash** — the first 8 chars of `sha1` over the verbatim evidence text. The ledger matches on this, so a marker whose text changed correctly re-surfaces.
- **age**, where knowable — `git blame -L <line>,<line> -- <file>` on a code marker gives the commit date. An item that's been sitting for a year is different information from one added yesterday.

### 1a. Code markers

Grep the addon's own `.lua` and `.xml` files — **exclude `libs/`, `Libs/`, and any vendored library directory**:

- `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `NOTE:` followed by deferral language
- prose deferrals in comments: `for now`, `temporary`, `revisit`, `later`, `placeholder`, `stub`, `not implemented`, `come back to`, `once we`
- **stub functions** — a function whose body is empty, is only a comment, or only `return` / `return nil`
- **commented-out blocks** — three or more consecutive commented lines that parse as Lua rather than as prose
- **hardcoded values flagged as provisional** — a literal on a line whose comment matches the deferral vocabulary above

Read enough surrounding lines to state what the marker actually asks for. A bare `-- TODO` with no context is itself a finding ("marker with no stated intent").

### 1b. Docs and frozen artifacts

- `README.md`, root `CLAUDE.md`, `docs/agent-context.md`, `docs/*.md` — open questions, "not yet", "planned", "TBD", "known issue" phrasing
- `docs/ARCHITECTURE.md` → **Known Limitations** section, every entry
- `CHANGELOG.md` → an `Unreleased` section with content in it
- `TODO.md` if present — every unchecked item

Then the high-value one: **unexecuted plan items.** Find the newest `docs/audits/<YYYY-MM-DD>/05_EXECUTION_PLAN.md` and the newest `docs/reviews/<YYYY-MM-DD>/04_EXECUTION_PLAN.md`. For each step or deviation ID they list, check the current code to see whether it was actually carried out. Report each as executed / not executed / partially executed, **with the evidence you used to decide** — a plan row is only a pending item if the code still shows the pre-remediation state. Carry the original deviation/finding ID into your item's evidence so it stays traceable back to the frozen bundle.

Older audit/review bundles are frozen history; don't re-litigate them. If the newest bundle is older than the newest one you can see in a directory listing, you read the wrong one — sort by date, take the latest.

### 1c. Git and GitHub

- `gh issue list --state open --limit 100` — one item per open issue. If `gh` is missing, unauthenticated, or the repo has no GitHub remote, **skip this sweep and say so in the report**; it is not a failure.
- `git stash list` — each stash is unfinished work
- `git status --porcelain` — uncommitted changes in the working tree
- `git log --oneline -50` — subjects/bodies containing `follow-up`, `followup`, `temporary`, `revert later`, `part 1`, `WIP`, `first pass`

### 1d. Claude memory

Look under `~/.claude/projects/<cwd-path-slug>/memory/` (the slug is the absolute cwd with `/` replaced by `-`). Read `MEMORY.md` and the entries it indexes. Surface entries that record a decision, constraint, or user instruction **with no corresponding change in the code or docs** — a memory saying "user wants X" where X isn't there yet is a pending action.

Memory entries reflect what was true when written. Before surfacing one, verify the file, function, or flag it names still exists.

## Step 2 — Bucketize

Classify each item on two axes.

**Type:**
- `Decision` — a call the user has to make; nobody can act until they do
- `Action` — the work is already identified and agreed, it just hasn't been done
- `Deferred` — explicitly postponed at some earlier point (by a ledger entry, a comment saying so, or a plan row marked deferred)

**Severity**, each asserted with a one-line justification so the ranking is arguable rather than decorative:
- `Critical` — taint, combat-lockdown breakage, saved-variable corruption or data loss, an error thrown on a common path
- `High` — a user-visible defect, or a deviation from the Ka0s WoW Addon Standard carried over from an audit bundle
- `Medium` — maintainability: a stub that callers depend on, drift between code and docs, a dead code path
- `Low` — polish, naming, cosmetic, speculative-future notes

**Ledger reconciliation.** For each item, look for a `docs/pending/LEDGER.md` row with the same ID *and* the same evidence hash:
- match found, decision was `done` or `wont-do` → **drop it entirely.** It is closed. Don't list it, don't count it, don't mention it in the report. These two are terminal: the work happened, or the user decided it never will. Either way it is no longer pending and must not surface again.
- match found, decision was `deferred` → file under **Previously deferred**; don't interview it. Deferral is *not* terminal — it's a "not now", so it stays visible as a collapsed count.
- ID matches but hash differs → the item changed since the decision, including if that decision was `done` or `wont-do`. Interview it, and say in the question that it was previously decided, what the decision was, and that the evidence has since changed.
- no match → new item, interview it

The distinction that matters: **`deferred` keeps an item alive and quiet; `wont-do` kills it.** If a user has to keep re-declining the same thing, the command is broken.

Print the inventory as a table grouped by severity (Critical first), showing ID, type, location, and a one-line summary — plus a collapsed count line for **Previously deferred**. Do not print the full evidence for every item here; that's noise. Print evidence when you interview the item.

If the sweep found nothing, say so plainly and stop. That's a good outcome, not a failed run.

## Step 3 — Interview

One item at a time, **most severe first**, using `AskUserQuestion`. Never batch. Never summarize a group as "and 12 more like this" and ask for one blanket call — the point of this command is per-item judgment.

For each item, show its verbatim evidence and location, then offer:
- **2–3 concrete resolution options specific to that item.** Not "fix it" / "don't fix it" — say what fixing it means here. For a stub function: implement it / delete it and its callers / leave the stub and document the limitation. For an unexecuted audit deviation: apply the remediation the bundle already designed / apply a different fix you describe / accept the deviation.
- **"Defer for now"** — always present, second-to-last. A "not now": the item stays on the books and reappears as a collapsed line next run. Note what deferring costs (nothing, usually; say so if it's not nothing).
- **"Will not do"** — always present, always last. A permanent close: the item is never raised again. Say plainly in the option text that this is permanent, and say what stays behind if they pick it (the TODO comment still sits in the code, the deviation stays in the frozen audit bundle, the issue stays open on GitHub) so the choice is made with eyes open.

The user can always answer free-text instead of picking. If they do, take their answer over your options.

### Follow-through on "will not do"

The ledger alone is enough to stop the item re-surfacing, so **no further action is required** and none is taken by default. But a dead marker left in the code is a trap for the next reader, so where there's an obvious tidy-up, offer it as a single yes/no follow-up:

- **code marker** → remove the `TODO`/`FIXME`, or rewrite it as a statement of intent (`-- Deliberately not handled: <reason>`). Prefer rewriting over deleting when the comment explains a real constraint.
- **doc entry** (Known Limitations, `Unreleased`, `TODO.md`) → leave it if it documents a genuine limitation; remove it if it only tracked intent to change.
- **open GitHub issue** → offer to close it with a comment explaining the decision. **Requires explicit confirmation** — closing someone's issue is outward-facing and visible to others. Default is no: the ledger already keeps it from re-surfacing locally.

Never bundle these into the main decision. Ask separately, accept a plain no, and record the answer in the ledger's rationale.

### Stopping early

If the user says to stop interviewing partway through, treat every un-interviewed item as **deferred** — never as `wont-do`. Silence is "not now", not "never". Then go to Step 4 with what you have.

## Step 3.5 — Branch decision

Before touching a single file, count the accepted items. If **five or more** were accepted, **or any accepted item is Critical**, and the current branch is `master` or `main`, propose a working branch:

> "That's N accepted items on `master`. Want me to branch first? Suggested: `pending/<YYYY-MM-DD>`."

Ask; don't just do it. If the user declines, or the set is small, or you're already on a non-default branch, proceed on the current branch.

## Step 4 — Implement

Only the accepted items. Group the work by file so each file is touched once.

- Use `Edit` for surgical changes; `Write` only when a file is being created or fully replaced.
- **Preserve line endings.** Detect each file's existing endings (LF or CRLF) and write the same.
- When an accepted item's resolution is "implement per the audit bundle", follow the remediation the bundle's `04_TECHNICAL_DESIGN.md` already specified rather than inventing a new one.
- If an item turns out to be un-implementable once you're in the code (the premise was wrong, it's already done, it conflicts with another accepted item), **stop on that item and tell the user** — don't improvise a different change.

When the edits are in, run the test battery if the addon has one — luacheck, the headless `tests/` harness, a Makefile `test` target. Report the result. If something you changed broke a test, fix it or revert that item and say which.

## Step 5 — Ledger

Write `docs/pending/LEDGER.md` (create `docs/pending/` if needed). Merge with the existing file — never clobber rows for items outside this run.

Format: a header explaining what the file is and that `/wow-addon:pending` maintains it, then one table with columns **ID | Evidence hash | Source | Decision | Date | Rationale**.

`Decision` is exactly one of:

| Value | Meaning | Re-surfaces? |
|---|---|---|
| `done` | Implemented this run | No — closed |
| `wont-do` | User decided it will never be done | No — closed |
| `deferred` | Not now; still on the books | Yes, as a collapsed count |

`Rationale` is the user's reason in one line — their words where they gave them. For `wont-do` the rationale is the most valuable column in the file: it's what stops a future reader (or a future agent) from re-opening a settled question. Never leave it blank; if the user gave no reason, write what you understood their reason to be and mark it as inferred.

The two closed states are load-bearing. Getting a row's decision wrong means either losing real work (`wont-do` on something the user wanted) or nagging them forever (`deferred` on something they closed). If you're unsure which the user meant, ask rather than guess.

## Step 6 — Report

Print:
- **Implemented** — item ID, what changed, files touched
- **Will not do** — item ID and reason, plus any follow-through taken (marker rewritten, issue closed). Show these once, here, so the user can see what they just closed permanently — then never again.
- **Deferred** — item ID and one-line reason (including anything auto-deferred by an early stop)
- **Previously deferred** — count only, with a pointer to the ledger
- **Skipped sweeps** — any source that couldn't run (no `gh`, no memory dir, no audit bundle) and why
- **Blocked** — anything accepted but not implementable, with what stopped you
- Test results, if a battery ran
- A reminder to review the diff before committing

## Hard rules

- **Don't commit.** Committing is `/wow-addon:commit`'s job.
- **Don't bump the version.** That's `/wow-addon:bump-version`'s job, even if an accepted item is about the version.
- **Don't act on an item the user didn't accept.** Deferring and "will not do" are real answers; both leave the code untouched unless the user separately opted into a follow-through tidy-up.
- **Don't resurrect closed items.** A `done` or `wont-do` ledger row with a matching evidence hash means the question is settled. Don't surface it, don't count it, don't "just check in" about it. The only thing that re-opens it is the evidence itself changing.
- **Don't infer "will not do" from silence.** Only a user explicitly choosing it makes an item `wont-do`. An early stop, a skipped question, or an ambiguous answer is `deferred`.
- **Don't invent pending items.** Every item traces to verbatim evidence at a real location. If you think something *should* be done but nothing in the repo, docs, issues, or memory says so, that's your opinion — leave it out, or raise it once in the report under a clearly labelled "Not a pending item, but noticed" line.
- **Don't edit frozen artifacts.** `docs/audits/<date>/` and `docs/reviews/<date>/` bundles are history. Implement their unexecuted items in the code; leave the bundles as written.
- **Don't re-interview settled items.** The ledger exists so a deferral means something.
- **Don't touch `libs/`** or any vendored library.

---
description: Triage every `[untriaged]` GitHub issue on the addon's repo — one at a time, most severe first, with its evidence in front of you. Each becomes `[triaged]` (not now), `[will-not-do]` (never), or `[done]` (already true). Decision-only: it records your call and rewrites the issue, and never changes code. GitHub writes run in background subagents so the interview never waits on the network. Discovery is `/wow-addon:issue-audit`.
argument-hint: [here|all|<repo>]
allowed-tools: [Read, Glob, Grep, Bash, AskUserQuestion, Task]
---

Put every untriaged item to a human, one at a time, and record what they decide.

This is the second half of the pair. `/wow-addon:issue-audit` sweeps the repo and files what it finds as `[untriaged]` — seen, but explicitly not decided. This command is where those become decisions. It changes **the issue store only**: no code, no docs, no commits.

## The vocabulary

| Status | Prefix | GitHub state | Meaning |
|---|---|---|---|
| `done` | `[done]` | closed | Implemented. Terminal |
| `wont-do` | `[will-not-do]` | closed | Will never be done. Terminal |
| `triaged` | `[triaged]` | open | Decided: not now. Still on the books |
| `untriaged` | `[untriaged]` | open | Never put to the user. **The input to this command** |

The distinction that carries the most weight: **`triaged` keeps an item alive and quiet; `will-not-do` kills it.** If someone has to keep re-declining the same thing, this command is broken. Equally, a `will-not-do` on something they actually wanted loses real work. When you can't tell which they meant, **ask again** rather than guess.

**GitHub API guardrail.** Use the `gh` CLI subcommands — `gh issue list`, `gh issue edit`, `gh issue close`, `gh issue comment`, `gh issue view` — with `--json` where structured data is needed. **Never use `gh api graphql`** and never hand-roll GraphQL against `api.github.com/graphql`; if REST is genuinely unavoidable use `gh api repos/{owner}/{repo}/issues`. Listing by status is a **title-prefix filter**, not a label query.

## Step 0 — Resolve the scope and read the queue

The `$ARGUMENTS` token:

- **absent, or `here`** → the repo at the cwd. **This is the default.**
- **`all`** → every addon repo in the collection, roster read from `WowAddonStandards/standards/ADDONS.md`; if unreachable, fall back to sibling directories with a `.toc` and **say the roster was inferred**.
- **a repo name** → that repo alone, matched case-insensitively. No match → say so, list the valid names, stop.

If the cwd is not an addon repo and no scope was given, **ask**. Don't guess.

Preflight `gh auth status` and `gh repo view --json nameWithOwner`. Either failing is **fatal** — the queue lives on GitHub and so does the answer. Say so and stop; never write a local file instead.

Read the queue:

```
gh issue list --state open --limit 200 --json number,title,body,createdAt,url
```

Take the issues whose title starts with `[untriaged]`. Also pick up **stray issues** — open issues with no recognised prefix, filed from the web UI or by someone not using these commands. Repair each on sight with `gh issue edit <n> --title "[untriaged] <existing title>"`, keeping the original title text exactly, and **report every repair**; then triage it like any other. An issue that reaches you without a prefix is still real work, and the one thing that must never happen is it going unseen.

If the queue is empty, say so plainly and stop. Nothing to decide is a good outcome.

**On an `all`-scope run, do one repo at a time and say which repo you're in before its first question.** Twenty questions with no sense of place is how people lose track of what they just agreed to.

## Step 1 — Order the queue

Read each issue's body for its `Severity`, `Location` and `Evidence`. Sort **most severe first** (`Critical`, `High`, `Medium`, `Low`), and within a severity, oldest first — an item that has been sitting for months has earned its turn ahead of one filed this morning.

Print the queue as a table — number, severity, location, one-line summary — then say how many there are and ask whether to go through them all now or stop after a given number. **Twenty decisions is a long sitting.** Someone who wanted to clear three should be able to.

## Step 2 — Interview

One item at a time, using `AskUserQuestion`. **Never batch.** Never summarize a group as "and 12 more like this" and ask for one blanket call — per-item judgment is the entire point of this command.

For each item, show its **verbatim evidence** and its **location** first, then offer:

- **2–3 concrete resolutions specific to that item.** Not "fix it" / "don't fix it" — say what fixing it would mean *here*. For a stub: implement it / delete it and its callers / leave it and document the limitation. For an unexecuted audit deviation: apply the remediation the bundle already designed / apply a different fix you describe / accept the deviation.
- **"Keep it open — real work, not now"** — always present. The issue stays open as `[triaged]` and comes back as a collapsed count, not a question. (All three options below are triage outcomes; this is the one that leaves the work on the books.)
- **"Will not do"** — always present, always last. A permanent close. Say plainly in the option text that it is permanent, and say what stays behind (the `TODO` still sits in the code, the deviation stays in the frozen bundle) so the choice is made with eyes open.

The user can always answer free-text instead of picking. **If they do, take their answer over your options** — the options are a convenience, not a cage.

**Where a resolution means "do the work":** this command does not do the work. Record it as `[triaged]` with the chosen approach in the decision comment, so whoever picks it up starts from a decision rather than a blank page. Say that plainly when they choose it — "I'll record the approach; the change itself is a separate session" — so nobody finishes triage believing code was written.

**The `[done]` case is narrow and needs evidence.** Only mark an item `[done]` when the work is *already true in the repo* — the marker is stale, the plan row was executed, the limitation no longer applies. Verify it in the code before recording it, quote what you checked, and say so. Never mark something `[done]` because the user agreed it *should* be done.

**Everything recorded here is public.** Say this once, up front, before the first question — not buried in an option label and never left to be discovered from a notification. Every decision becomes a title and a body on a public repo, and whoever watches it gets mailed.

### Stopping early

If the user stops partway through, **leave every un-interviewed issue exactly as it is** — still `[untriaged]`, still open, untouched. They weren't declined or postponed; they were never asked. Silence is not a decision and must never be recorded as one.

This is the one place this command is meaningfully safer than the old fused version: the queue is already in the store, so an early stop loses nothing and needs no consent to publish anything. Just report where you stopped.

## Step 3 — Record the decision, then write it in the background

**Never make the user wait on `gh`.** The moment an answer arrives, write it to the run journal and move to the next question. The GitHub calls happen in a background subagent while the interview continues. A triage sitting is a conversation; three `gh` round trips between every question turns it into a progress bar, and the whole reason this command was split out of `issue-audit` was to make the conversation cheap.

### 3a. Journal the answer first — synchronously, before anything else

Append one line to the run journal, a JSONL file in the session scratchpad named for this run (e.g. `triage-<YYYYMMDD-HHMMSS>.jsonl`):

```json
{"repo":"PanelMaster","issue":4,"title":"<existing title text, prefix stripped>","decision":"triaged","approach":"<the resolution chosen, if any>","rationale":"<the user's words>","asked_at":"<timestamp>"}
```

This write is **synchronous and happens before the next question**, because the journal — not GitHub — is what makes an answer durable. If the session dies, the network drops, or a subagent fails, every decision the user actually made is still on disk and can be replayed. Losing someone's considered judgment to a failed API call is the worst outcome this command has.

### 3b. Spawn a background subagent to do the writing

Once journalled, dispatch a subagent to carry that one decision to GitHub, and **immediately continue interviewing**. Give it the repo, issue number, decision, approach and rationale, and these instructions:

| Decision | Calls |
|---|---|
| `triaged` | `gh issue edit <n> --title "[triaged] <title>"` + `gh issue comment <n>` with the decision block. Stays open. |
| `will-not-do` | `gh issue edit <n> --title "[will-not-do] <title>"` + comment + `gh issue close <n> --reason "not planned"` |
| `done` | `gh issue edit <n> --title "[done] <title>"` + comment + `gh issue close <n> --reason completed` |

Constraints every subagent carries:

- **It decides nothing.** It applies one recorded decision verbatim. It must never re-word a rationale, never pick a status, never ask anything, and never touch an issue other than the one it was given.
- **Space the calls out** — a few seconds between mutations — and write **idempotently**: re-read the issue before editing if a call failed, so a timeout doesn't produce a double comment. `gh issue comment` is not idempotent by itself; check whether the decision block is already present before adding it.
- **One subagent per decision**, and keep at most a few in flight. They are writing to the same repo, and a burst is how a run gets rate-limited into a half-written state.
- **It reports its outcome** — which calls succeeded, which failed, and the resulting issue URL — so the parent can reconcile.

### 3c. Reconcile before reporting

The run is not finished when the last question is answered. It is finished when **every** subagent has returned. Before printing Step 4:

1. Wait for all of them.
2. Compare the journal against the outcomes, line by line. Every journalled decision must have a matching successful write.
3. Any decision with no successful write is **reported as unwritten**, with the issue number and what failed — never silently dropped, and never presented as though it landed. Say plainly that the decision is recorded in the journal and can be replayed, and give the journal path.

A decision the user made and GitHub never received is the one failure this command must never hide.

**Keep the existing title text; change only the prefix.** The title is how the item is recognised across runs and in `/wow-addon:issue-details`; rewriting it orphans every reference to it.

**Prefix and state must never disagree.** `[done]` and `[will-not-do]` are closed; `[triaged]` and `[untriaged]` are open. If you find one that disagrees, fix the state and say so in the report — that combination is a bug, and it is exactly what `/wow-addon:issue-summary` reports as an inconsistency.

The decision block appended as a comment:

```
### Triage decision

- **Decision:** triaged
- **Decided:** 2026-08-06
- **Approach:** <the resolution the user chose, if any>

### Rationale

<the user's reason, in their words>
```

- **Rationale is never blank.** For `[will-not-do]` it is **the most valuable field in the store** — it is what stops a future reader, or a future agent, re-opening a settled question, and it is what `/wow-addon:harvest-standards` mines to find rules the collection has collectively declined. If the user gave no reason, write what you understood their reason to be and **mark it inferred**.
- Comment rather than rewriting the body: the body is the audit record of what was found, the comment is the record of what was decided, and keeping them separate means the evidence survives the decision.

### Follow-through on "will not do"

The closed issue is enough to stop the item re-surfacing, so **no further action is required and none is taken by default**. But a dead marker in the code is a trap for the next reader, so where there is an obvious tidy-up, offer it as a single yes/no — and note that carrying it out is a **code change this command will not make**. Record the answer in the rationale so the intent survives, and let the user make the edit in a normal session.

Never bundle this into the main decision. Ask separately, accept a plain no.

## Step 4 — Report

Print this **only after every subagent has returned** (Step 3c). It has two halves, because they can disagree: what was *decided*, and what was *written*.

**Decisions taken** — one row per item, straight from the journal, so this is complete even if a write failed:

| Repo | # | Decision | Approach | Rationale (one line) |
|---|---|---|---|---|

**Changes made** — what actually landed on GitHub, from the subagent outcomes:

| Repo | # | Title now | State | URL |
|---|---|---|---|---|

Then:

- **Will not do** — call these out again in prose with their reasons. They are permanent closes, and this is the one place the user sees the full set of things they just ended. Never fold them into a table row and move on.
- **Done** — issue number and the evidence you verified it against.
- **Unwritten decisions** — any journalled decision with no successful write: issue number, what failed, and the journal path so it can be replayed. **If this section is empty, say so explicitly** ("all N decisions written") rather than omitting it — its absence should never be something the reader has to infer.
- **Left untriaged** — count and why (stopped early, out of scope). Re-running resumes here.
- **Stray issues repaired** — every issue that gained a prefix, old title and new.
- **Fixed inconsistencies** — any prefix/state disagreement corrected, with both values.
- A reminder that **no code changed**, and what to run next if any triaged item is ready to be worked.

Keep the two halves separate even when they match perfectly. Collapsing them into one table is how "I decided this" quietly becomes indistinguishable from "and it was recorded", which is exactly the confusion the journal exists to prevent.

## Hard rules

- **Never change code, docs, or the working tree.** This command edits GitHub issues and nothing else. No `Edit`, no `Write`, no commits, no version bumps. If a decision implies a code change, it is recorded, not performed.
- **Never infer a decision from silence.** An early stop, a skipped question or an ambiguous answer leaves the issue `[untriaged]`. Only an explicit choice closes something.
- **Never batch the interview.** One item, one question, evidence shown.
- **Journal before dispatching, always.** The answer goes to disk synchronously before any subagent is spawned and before the next question is asked. A decision that exists only in a subagent's prompt is a decision one failed call away from being lost.
- **A write subagent never decides.** It applies one recorded decision verbatim — no re-wording, no status choice, no questions, and no touching any issue but its own.
- **Never report before reconciling.** Wait for every subagent, diff the journal against the outcomes, and report any decision that did not land as unwritten. Presenting a decision as recorded when GitHub never received it is the failure this whole mechanism exists to prevent.
- **Never mark `[done]` without verifying it in the repo** and quoting what you checked.
- **Never rewrite a title's text** — only its prefix.
- **Never bulk-close.** An issue whose evidence you can't find is not thereby stale; leave it.
- **Use the `gh` CLI subcommands.** Never `gh api graphql`.
- **Don't touch `libs/`** or any vendored library, and don't edit frozen `docs/audits/` or `docs/reviews/` bundles.

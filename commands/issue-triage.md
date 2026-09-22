---
description: Triage every `state:untriaged` GitHub issue on the addon's repo — one at a time, most severe first, with its evidence in front of you. Each becomes `state:triaged` (not now), `state:will-not-do` (never), or `state:done` (already true). Decision-only: it records your call by swapping the status label, and never changes code. GitHub writes run in background subagents so the interview never waits on the network. Discovery is `/wow-addon:issue-audit`.
argument-hint: [here|all|<repo>]
allowed-tools: [Read, Glob, Grep, Bash, AskUserQuestion, Task]
---

Put every untriaged item to a human, one at a time, and record what they decide.

This is the second half of the pair. `/wow-addon:issue-audit` sweeps the repo and files what it finds as `state:untriaged` — seen, but explicitly not decided. This command is where those become decisions. It changes **the issue store only**: no code, no docs, no commits.

## The vocabulary

**Status** — exactly one `state:` label per issue:

| Status | Label | Color | GitHub state | Meaning |
|---|---|---|---|---|
| done | `state:done` | green `00ff00` | closed | Implemented. Terminal |
| will-not-do | `state:will-not-do` | blue `0000ff` | closed | Will never be done. Terminal |
| triaged | `state:triaged` | yellow `ffff00` | open | Decided: not now. Still on the books |
| untriaged | `state:untriaged` | red `ff0000` | open | Never put to the user. **The input to this command** |

**Severity** — exactly one `severity:` label per issue. It is what this command **orders the queue by**, so it is load-bearing here rather than decorative:

| Severity | Label | Color | Meaning |
|---|---|---|---|
| Critical | `severity:critical` | red `110000` | Taint, combat-lockdown breakage, saved-variable corruption or data loss, an error on a common path |
| High | `severity:high` | orange `110800` | A user-visible defect, or a Ka0s standard deviation carried from an audit bundle |
| Medium | `severity:medium` | yellow `111100` | Maintainability: a stub callers depend on, code/doc drift, a dead path |
| Low | `severity:low` | green `001100` | Polish, naming, cosmetic, speculative-future notes |

**The labels are the data.** The title carries neither status nor severity — the old `[untriaged] …` title-prefix convention is **retired**. A stale prefix on an old issue is leftover text; strip it as part of the stray repair below and trust the label.

The distinction that carries the most weight: **`state:triaged` keeps an item alive and quiet; `state:will-not-do` kills it.** If someone has to keep re-declining the same thing, this command is broken. Equally, a `will-not-do` on something they actually wanted loses real work. When you can't tell which they meant, **ask again** rather than guess.

**GitHub API guardrail.** Use the `gh` CLI subcommands — `gh issue list`, `gh issue edit`, `gh issue close`, `gh issue comment`, `gh issue view`, `gh label list`, `gh label create` — with `--json` where structured data is needed. **Never use `gh api graphql`** and never hand-roll GraphQL against `api.github.com/graphql`; if REST is genuinely unavoidable use `gh api repos/{owner}/{repo}/issues`. Listing by status or severity is a plain **`--label` query**, not a title filter.

## Step 0 — Resolve the scope and read the queue

The `$ARGUMENTS` token:

- **absent, or `here`** → the repo at the cwd. **This is the default.**
- **`all`** → every addon repo in the collection, roster read from `WowAddonStandards/standards/ADDONS.md`; if unreachable, fall back to sibling directories with a `.toc` and **say the roster was inferred**.
- **a repo name** → that repo alone, matched case-insensitively. No match → say so, list the valid names, stop.

If the cwd is not an addon repo and no scope was given, **ask**. Don't guess.

Preflight `gh auth status` and `gh repo view --json nameWithOwner`. Either failing is **fatal** — the queue lives on GitHub and so does the answer. Say so and stop; never write a local file instead.

### Ensure the label set exists

Before any write, make sure the eight collection labels exist. `gh label create --force` creates a missing label and updates an existing one's color and description, so it is safe to run every time:

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

Read `gh label list --limit 100 --json name,color` first and run only the creates that are missing or wrong. A repo where the status labels are absent has never been swept — say so, because an empty queue there means "never audited", not "nothing pending".

Read the queue:

```
gh issue list --state open --limit 200 --json number,title,body,labels,createdAt,url
```

Take the issues carrying `state:untriaged`. Also pick up **stray issues** — open issues with **no** `state:` label, filed from the web UI or by someone not using these commands. Repair each on sight with `gh issue edit <n> --add-label "state:untriaged"`, and where the issue also carries no `severity:` label, assess one from its body and add it. If a legacy `[status]` title prefix is present, strip it in the same repair — `gh issue edit <n> --title "<title without the prefix>"` — keeping the rest of the title text exactly. **Report every repair**; then triage it like any other. An issue that reaches you without a status is still real work, and the one thing that must never happen is it going unseen.

### Resume check — before the first question, always

List `~/.claude/wow-addon/issue-triage/`. Any journal **missing its `complete` line** is a run that recorded decisions and never confirmed they landed — a crashed session, a killed process, a machine that went away mid-run.

For each such journal, read its `decision` lines and match them against its `outcome` lines. Decisions with no successful outcome are **unconfirmed**: the user made them, and nobody knows whether GitHub received them.

**Check the real state before offering anything.** For each unconfirmed decision, read the live issue (`gh issue view <n> -R <owner>/<repo> --json title,state,labels,comments`). Three cases:

- **Already applied** — the issue carries the decided `state:` label and the decision comment is present. The write landed and only the outcome line was lost. Append the missing `outcome` line and move on; **do not re-apply and do not re-ask**.
- **Not applied** — offer to replay it, showing the decision, its rationale and the issue. Replay is the same idempotent write as Step 3b.
- **Applied differently** — the issue now carries a different `state:` label than the journal records. Somebody or something changed it in between. **Do not overwrite it.** Report both values and leave it; a stale journal must never be allowed to revert a newer decision.

Then write the `complete` line to that old journal so it stops being offered.

**Never replay silently.** A decision from a previous session, possibly days old, being pushed to a public repo without the user seeing it is the same consent failure as filing an issue nobody asked for. Show what would be written and get a yes. If they decline, leave the journal unreconciled and say it will be offered again.

If no journals are incomplete, say nothing about it — a clean resume check is not news.

**On an `all`-scope run, do one repo at a time and say which repo you're in before its first question.** Twenty questions with no sense of place is how people lose track of what they just agreed to.

## Step 1 — Order the queue

**Sort by the `severity:` label, most severe first** (`severity:critical`, `severity:high`, `severity:medium`, `severity:low`), and within a severity, oldest first — an item that has been sitting for months has earned its turn ahead of one filed this morning. An issue with no severity label sorts **last** and is flagged in the queue table, because an unranked item is one nobody has sized, not one that is unimportant.

Read each issue's body for its `Location`, `Evidence` and `Severity rationale` — the rationale is the argument behind the label, and it is what the user needs in order to overrule it.

Print the queue as a table — number, severity, location, one-line summary — then say how many there are and ask whether to go through them all now or stop after a given number. **Twenty decisions is a long sitting.** Someone who wanted to clear three should be able to.

**If the user disputes a severity, change it.** `gh issue edit <n> --remove-label "severity:low" --add-label "severity:high"` is a legitimate write for this command and it re-orders the rest of the queue. Record the change in the journal and the report like any other write. Severity is a judgment call the label captured on the user's behalf; the user overruling it is the system working, not an exception to it.

## Step 2 — Interview

One item at a time, using `AskUserQuestion`. **Never batch.** Never summarize a group as "and 12 more like this" and ask for one blanket call — per-item judgment is the entire point of this command.

For each item, show its **severity**, its **verbatim evidence** and its **location** first, then offer:

- **2–3 concrete resolutions specific to that item.** Not "fix it" / "don't fix it" — say what fixing it would mean *here*. For a stub: implement it / delete it and its callers / leave it and document the limitation. For an unexecuted audit deviation: apply the remediation the bundle already designed / apply a different fix you describe / accept the deviation.
- **"Keep it open — real work, not now"** — always present. The issue stays open as `state:triaged` and comes back as a collapsed count, not a question. (All three options below are triage outcomes; this is the one that leaves the work on the books.)
- **"Will not do"** — always present, always last. A permanent close. Say plainly in the option text that it is permanent, and say what stays behind (the `TODO` still sits in the code, the deviation stays in the frozen bundle) so the choice is made with eyes open.

The user can always answer free-text instead of picking. **If they do, take their answer over your options** — the options are a convenience, not a cage.

**Where a resolution means "do the work":** this command does not do the work. Record it as `state:triaged` with the chosen approach in the decision comment, so whoever picks it up starts from a decision rather than a blank page. Say that plainly when they choose it — "I'll record the approach; the change itself is a separate session" — so nobody finishes triage believing code was written.

**The `state:done` case is narrow and needs evidence.** Only mark an item done when the work is *already true in the repo* — the marker is stale, the plan row was executed, the limitation no longer applies. Verify it in the code before recording it, quote what you checked, and say so. Never mark something done because the user agreed it *should* be done.

**Everything recorded here is public.** Say this once, up front, before the first question — not buried in an option label and never left to be discovered from a notification. Every decision becomes a label and a body on a public repo, and whoever watches it gets mailed.

### Stopping early

If the user stops partway through, **leave every un-interviewed issue exactly as it is** — still `state:untriaged`, still open, untouched. They weren't declined or postponed; they were never asked. Silence is not a decision and must never be recorded as one.

This is the one place this command is meaningfully safer than the old fused version: the queue is already in the store, so an early stop loses nothing and needs no consent to publish anything. Just report where you stopped.

## Step 3 — Record the decision, then write it in the background

**Never make the user wait on `gh`.** The moment an answer arrives, write it to the run journal and move to the next question. The GitHub calls happen in a background subagent while the interview continues. A triage sitting is a conversation; three `gh` round trips between every question turns it into a progress bar, and the whole reason this command was split out of `issue-audit` was to make the conversation cheap.

### 3a. Journal the answer first — synchronously, before anything else

The journal lives **outside the session**, under:

```
~/.claude/wow-addon/issue-triage/<scope>-<YYYYMMDD-HHMMSS>.jsonl
```

`<scope>` is the repo name, or `all` for a collection run. **The timestamp is to the second, and that is what makes the file unique** — two runs against the same repo on the same day must never share a journal, or one run's reconciliation checks itself against another run's decisions.

It is deliberately **not** in the session scratchpad. A scratchpad journal survives a failed API call but not a crashed session, a new session, or a `/tmp` sweep — and "your decision is safe on disk" is worth nothing if the only process that can read it is the one that just died.

Create the file with a run header, then append one line per event. Four line types, distinguished by `type`:

```json
{"type":"run","scope":"all","started":"2026-08-07T00:31:12Z","queue":[{"repo":"PanelMaster","issue":4}]}
{"type":"decision","repo":"PanelMaster","issue":4,"title":"<title text>","severity":"medium","severity_changed_from":null,"decision":"triaged","approach":"<resolution chosen, if any>","rationale":"<the user's words>","asked_at":"2026-08-07T00:33:40Z"}
{"type":"outcome","repo":"PanelMaster","issue":4,"ok":true,"state":"OPEN","labels":["state:triaged","severity:medium"],"url":"...","detail":"label swap+comment succeeded"}
{"type":"complete","reconciled":"2026-08-07T00:46:02Z","decisions":11,"written":11,"unwritten":0}
```

The **decision** line is written **synchronously, before the next question is asked and before any subagent is spawned**. That ordering is the whole mechanism: a decision that exists only in a subagent's prompt is one failed call away from being lost, and losing someone's considered judgment is the worst outcome this command has.

**A journal with no `complete` line is an unreconciled run.** That is the only signal Step 0's resume check uses, so never write one until Step 3c has actually reconciled.

Journals are kept after completion — they are the local record of what was decided and when. Prune by hand if the directory grows; never automatically, and never as part of a run.

### 3b. Spawn a background subagent to do the writing

Once journalled, dispatch a subagent to carry that one decision to GitHub, and **immediately continue interviewing**. Give it the repo, issue number, decision, approach, rationale and any severity change, and these instructions:

| Decision | Calls |
|---|---|
| `triaged` | `gh issue edit <n> --remove-label "state:untriaged" --add-label "state:triaged"` + `gh issue comment <n>` with the decision block. Stays open. |
| `will-not-do` | `gh issue edit <n> --remove-label "state:untriaged" --add-label "state:will-not-do"` + comment + `gh issue close <n> --reason "not planned"` |
| `done` | `gh issue edit <n> --remove-label "state:untriaged" --add-label "state:done"` + comment + `gh issue close <n> --reason completed` |

A severity change rides along in the same `gh issue edit` call: `--remove-label "severity:<old>" --add-label "severity:<new>"`.

Constraints every subagent carries:

- **It decides nothing.** It applies one recorded decision verbatim. It must never re-word a rationale, never pick a status or a severity, never ask anything, and never touch an issue other than the one it was given.
- **The status label swap is one call.** `--remove-label` and `--add-label` in the same `gh issue edit` invocation, so the issue is never briefly carrying two `state:` labels or none — a half-applied swap is exactly what a concurrent read of the store would misreport.
- **Space the calls out** — a few seconds between mutations — and write **idempotently**: re-read the issue before editing if a call failed, so a timeout doesn't produce a double comment. `gh issue comment` is not idempotent by itself; check whether the decision block is already present before adding it.
- **One subagent per decision**, and keep at most a few in flight. They are writing to the same repo, and a burst is how a run gets rate-limited into a half-written state.
- **It reports its outcome** — which calls succeeded, which failed, and the resulting issue URL and label set — so the parent can reconcile.

### 3c. Reconcile before reporting

The run is not finished when the last question is answered. It is finished when **every** subagent has returned. Before printing Step 4:

1. Wait for all of them, appending each returned result as an `outcome` line.
2. Compare `decision` lines against `outcome` lines. Every decision must have a matching successful write.
3. **Verify against GitHub, not against the subagents' own reports.** Re-read each touched issue (`gh issue view <n> --json title,state,labels,comments`) and confirm the `state:` label, the `severity:` label, the open/closed state and the presence of the decision comment. A subagent reporting success is evidence, not proof — the point of reconciling is to check the store, and checking it against the same process that wrote it checks nothing.
4. Any decision with no confirmed write is **reported as unwritten**, with the issue number and what failed — never silently dropped, never presented as though it landed. Give the journal path and say it can be replayed.
5. **Write the `complete` line last**, carrying the counts. Only write it if step 3 actually verified; a `complete` line on an unverified run turns the resume check into a lie, and the resume check is the entire reason the journal outlives the session.

A decision the user made and GitHub never received is the one failure this command must never hide.

**Never change the title.** The title is how the item is recognized across runs and in `/wow-addon:issue-details`; rewriting it orphans every reference to it. The single exception is stripping a legacy `[status]` prefix during the Step 0 stray repair, which is announced.

**Exactly one `state:` label, and it must not disagree with the GitHub state.** `state:done` and `state:will-not-do` are closed; `state:triaged` and `state:untriaged` are open. If you find one that disagrees, fix the state and say so in the report — that combination is a bug, and it is exactly what `/wow-addon:issue-summary` reports as an inconsistency. Two `state:` labels on one issue is the same class of bug: report it and leave it rather than guessing which is current.

The decision block appended as a comment:

```
### Triage decision

- **Decision:** triaged
- **Severity:** medium
- **Decided:** 2026-08-06
- **Approach:** <the resolution the user chose, if any>

### Rationale

<the user's reason, in their words>
```

- **Rationale is never blank.** For `state:will-not-do` it is **the most valuable field in the store** — it is what stops a future reader, or a future agent, re-opening a settled question, and it is what `/wow-addon:harvest-standards` mines to find rules the collection has collectively declined. If the user gave no reason, write what you understood their reason to be and **mark it inferred**.
- Comment rather than rewriting the body: the body is the audit record of what was found, the comment is the record of what was decided, and keeping them separate means the evidence survives the decision.

### Follow-through on "will not do"

The closed issue is enough to stop the item re-surfacing, so **no further action is required and none is taken by default**. But a dead marker in the code is a trap for the next reader, so where there is an obvious tidy-up, offer it as a single yes/no — and note that carrying it out is a **code change this command will not make**. Record the answer in the rationale so the intent survives, and let the user make the edit in a normal session.

Never bundle this into the main decision. Ask separately, accept a plain no.

## Step 4 — Report

Print this **only after every subagent has returned** (Step 3c). It has two halves, because they can disagree: what was *decided*, and what was *written*.

**Decisions taken** — one row per item, straight from the journal, so this is complete even if a write failed:

| Repo | # | Severity | Decision | Approach | Rationale (one line) |
|---|---|---|---|---|---|

**Changes made** — what actually landed on GitHub, from the subagent outcomes:

| Repo | # | Labels now | State | URL |
|---|---|---|---|---|

Then:

- **Will not do** — call these out again in prose with their reasons. They are permanent closes, and this is the one place the user sees the full set of things they just ended. Never fold them into a table row and move on.
- **Done** — issue number and the evidence you verified it against.
- **Severity changes** — every issue whose `severity:` label the user overruled, old and new, since that re-ordered the queue everyone else was judged in.
- **Unwritten decisions** — any journalled decision with no successful write: issue number, what failed, and the journal path so it can be replayed. **If this section is empty, say so explicitly** ("all N decisions written") rather than omitting it — its absence should never be something the reader has to infer.
- **Left untriaged** — count and why (stopped early, out of scope), with its severity split. Re-running resumes here.
- **Stray issues repaired** — every issue that gained a label or lost a legacy title prefix, old and new.
- **Fixed inconsistencies** — any label/state disagreement corrected, with both values.
- A reminder that **no code changed**, and what to run next if any triaged item is ready to be worked.

Keep the two halves separate even when they match perfectly. Collapsing them into one table is how "I decided this" quietly becomes indistinguishable from "and it was recorded", which is exactly the confusion the journal exists to prevent.

## Hard rules

- **Never change code, docs, or the working tree.** This command edits GitHub issues and nothing else. No `Edit`, no `Write`, no commits, no version bumps. If a decision implies a code change, it is recorded, not performed.
- **Never infer a decision from silence.** An early stop, a skipped question or an ambiguous answer leaves the issue `state:untriaged`. Only an explicit choice closes something.
- **Never batch the interview.** One item, one question, evidence shown.
- **Journal before dispatching, always.** The answer goes to disk synchronously before any subagent is spawned and before the next question is asked. A decision that exists only in a subagent's prompt is a decision one failed call away from being lost.
- **A write subagent never decides.** It applies one recorded decision verbatim — no re-wording, no status choice, no severity choice, no questions, and no touching any issue but its own.
- **Never report before reconciling.** Wait for every subagent, verify each touched issue against GitHub itself, and report any decision that did not land as unwritten. Presenting a decision as recorded when GitHub never received it is the failure this whole mechanism exists to prevent.
- **Never write the `complete` line without verifying.** It is the only marker distinguishing a finished run from an abandoned one; writing it on an unverified run makes the resume check silently useless.
- **Never replay a previous run's decision silently.** A journalled decision from an earlier session is still the user's, but pushing it to a public repo without showing them is the same consent failure as filing an issue nobody asked for. Show it, get a yes.
- **Never let a stale journal overwrite a newer decision.** If an issue's current `state:` label differs from what the journal recorded, report both and leave it alone.
- **Never mark `state:done` without verifying it in the repo** and quoting what you checked.
- **Never rewrite a title.** The only permitted title edit is stripping a legacy `[status]` prefix during the stray repair, and it is announced.
- **Never change a severity on your own initiative.** A `severity:` label moves only when the user says so during the interview, or when a stray issue had none at all.
- **Never bulk-close.** An issue whose evidence you can't find is not thereby stale; leave it.
- **Use the `gh` CLI subcommands.** Never `gh api graphql`.
- **Don't touch `libs/`** or any vendored library, and don't edit frozen `docs/audits/` or `docs/reviews/` bundles.

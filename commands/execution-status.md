---
description: Status overview of the work planned in the current conversation. Covers what is done, what is in flight, what is left, a percent complete and an honest time to finish. Works for a single multi-step task, and for long runs driven by subagents and dynamic workflows across several repos. Reads a documented plan (a plan file with a status ledger or checkboxes) when one exists, and reconciles it against git commits, live background work and everything else the conversation planned. Read-only. Use it whenever the user asks where things stand, how far along the work is, what is left, how long until it is done, or wants a progress summary of an ongoing effort, even without the word "status".
argument-hint: [plan-path] [brief]
allowed-tools: [Bash, Read, Glob, Grep, TaskOutput]
---

Tell the user where the planned work stands, in one screen:
- what is done;
- what is running right now;
- what is left, in order;
- how complete it is as a percentage;
- when it will likely finish.

The report has to be **true**, so everything here is about evidence. People make decisions from a status report, and one that rounds "coded" up to "done" or invents an ETA is worse than none.

This command **only reads**. It never ticks a ledger row, commits, restarts work or messages a running agent. A status check that changes the thing it measures has stopped being a status check.

## Step 1 — Establish what was planned

The denominator is **everything planned in this conversation**, not only what a plan file lists. Build it from these sources, in order, and merge them:

1. **The documented plan, if there is one.** Use `$ARGUMENTS` if it names a path. Otherwise, look for the plan the conversation itself named or wrote. The usual homes are:
   - `docs/superpowers/plans/*.md`
   - `docs/superpowers/specs/*.md` (for requirement IDs)
   - `_dev/PLAN*.md`
   - a `TODO.md`
   - a memory note that points at a plan

   Read its status ledger or checkbox list. If there is a ledger (task, status, commit), it gives you the task list, its phases and checkpoints, and the order the work runs in. Several plan files may be live at once, one per repo or phase; read each one the conversation used.
2. **What the conversation added on top.** Include:
   - requests the user made after the plan was written;
   - steps you promised ("then I'll run the final review");
   - the todo list, if the session keeps one;
   - follow-ups a finished task handed back.

   A plan file written at the start rarely lists the last three things the user asked for. Leaving them out overstates completion.
3. **Single-task mode.** If there is no plan file, the plan is the steps this task needs: the ones you listed or committed to in the conversation, or, failing that, the steps the request clearly implies. Use those as the units, and say in the report that they come from the conversation rather than from a plan document.

Give each unit a stable label and a name: the plan's task IDs (`A1`, `D6`) when it has them, otherwise short names. Group them the way the plan groups them (phases, repos or tracks); in single-task mode a flat list is fine.

## Step 2 — Gather evidence of progress

A ledger says what someone *wrote down*. Commits and running processes say what *happened*. Read both, and do not rely on either alone.

- **Git, per repo the work touches.** For each repo:
  - `git -C <repo> branch --show-current`
  - `git log --oneline <base>..HEAD` with times: `--format='%h %ad %s' --date=format:%H:%M`, where the base is the branch the work split from, usually `master` or `main`
  - `git status --short`

  Branch names, sibling repos and base branches come from the plan or the conversation. A multi-repo effort needs every repo, not just the cwd.
- **Live background work.**
  - For every workflow, subagent or background shell the conversation launched, check its state without waiting: `TaskOutput` with `block: false` and a short timeout. Record running, completed, failed or killed.
  - A workflow's `runId` and its `journal.jsonl` show which agents have finished, when you need that detail.
  - **Never wait on a running task, and never message one to ask how it is doing.** Messaging a workflow's subagent can wake a *duplicate* of it that repeats its work.
- **The clock.** Run `date +%H:%M` (and the date when the work spans days). Every time in the report is measured from this.

## Step 3 — Reconcile into statuses

Give each unit exactly one status, and let the stronger evidence win:

| Status | Needs |
|---|---|
| **done** | A commit that delivers it (or, for a non-code step, its artifact), **and** nothing about it still in flight: its review has finished and its checkpoint has passed. A ledger row marked `done` whose commit you can find is done. |
| **coded, in review** | Its commits exist, but a review, a fix round or a gate on it is still running, or the ledger has not caught up. Name it separately: it is close to done but not done. |
| **in progress** | A live agent or task is on it now, or partial commits exist. |
| **queued** | Not started, and it waits on something named: an earlier task, a checkpoint, a release, the user. |
| **blocked** | It stopped on a decision, a failure or a missing prerequisite. Say which. |
| **dropped / deferred** | The user or the plan took it out of scope. It leaves the denominator, and the report says so. |

When the ledger and git disagree, trust git and name the gap. For example: "G1–G3 are committed but not yet ticked in the ledger." A ledger that lags is normal when the orchestrator updates it after a run. A ledger marked done with no commit behind it is a finding.

## Step 4 — Compute percent complete

- **Percent = done units ÷ planned units**, and the report says "n of m tasks". Count **coded, in review** separately, and put it in the headline too: "23 of 30 done, 3 more coded and in review".
- Count by units the plan defines, and name the unit. If the units vary a lot in size (a release versus a one-line fix), you may also give a weighted figure, but only with the weights stated. Never give a weighted number alone.
- Round to the nearest 5%. Precision beyond the evidence is noise.

## Step 5 — Estimate the time left

Estimate from **this effort's own pace**, never from a generic guess:

1. **Measure the pace.** Look at the commit timestamps of finished units of the same kind. For example, three panel tasks at 11:34, 12:06 and 12:28 is about 25 minutes each, review included. Use the median, and note an outlier rather than averaging it away.
2. **Scale by what remains, per track.** Remaining units multiplied by the pace, for each track that runs in sequence. Tracks that run **in parallel** overlap, so the time left is the *longest* track, not the sum.
3. **Add the fixed tail.** Final reviews, full test batteries, a release, a report: steps the plan runs once at the end, estimated from their own history if they have any, or stated as an assumption.
4. **Give a range and a clock time.** For example, "about 3–3½ hours, around 16:00–16:30 (it's 12:50 now)". Show the basis in a line or two, so the reader can redo the arithmetic.
5. **Name what could break the estimate.** Examples:
   - a task that may hit a platform limit;
   - a coverage test that may turn up more bugs than planned;
   - a decision that is waiting on the user.

With no finished units to measure (the first task is still running), say the pace is unmeasured. Give a rough range only with the assumption stated, or say you cannot estimate yet. A confident ETA made from nothing is the one number in this report that is easy to get wrong silently.

## Step 6 — The report

Use this shape. Drop a section that would be empty, except **Still to do**, which is written even when the answer is "nothing".

```
**~<P>% complete — <n> of <m> tasks done** (<k> more coded, in review). Likely done in **<range>, around <clock>** (it's <now>). <One sentence on what is running right now.>

| Phase | Tasks | Status |
|---|---|---|
| <phase name> | <count> | ✅ done / 🟡 x of y done; <what is running> / ⏳ queued after <X> / ⛔ blocked: <why> |

**Done since the last update** (or **Done so far**, the first time): what each finished unit delivered, in user terms, with the requirement or task IDs.

**Still to do**, in order: numbered, one line each, with what it depends on.

**How I estimated the time:** the pace measured, what remains per track, the parallel overlap, the fixed tail.

**Risks to the estimate:** only the real ones.

**Waiting on you:** decisions or checks only the user can make (merge, push, in-game checks). Leave it out when there are none.
```

- **Talk in outcomes, not mechanics.** "General → Containers is live and the Containers page is gone" tells the user more than "D2 done (bbdf178)". Keep commit hashes and run ids to where they help someone check the claim.
- **Write for a reader who has been away.** Spell out a task ID the first time it appears, with the name of what it builds.
- **`brief`** in `$ARGUMENTS` shortens it to the headline, the phase table and the next three steps.
- If this is not the first status report in the conversation, compare it with the last one: what moved, and whether the ETA held. A trend is only claimed against a report actually given.

## Hard rules

- **Read-only.** Never:
  - edit a ledger, plan, todo list or memory note;
  - commit or push;
  - restart, resume or stop background work;
  - message a running agent.

  Offer to update the ledger afterwards if it is stale, and wait for a yes.
- **Never block on running work.** Always call `TaskOutput` with `block: false`. The user asked for the status now, not when the work finishes.
- **Evidence or it did not happen.** Done needs a commit or an artifact. "An agent said it finished" is not enough when the commit is missing.
- **The denominator includes the whole conversation.** Every request and every promised step counts, not only what the plan file lists. Say where each came from when it matters.
- **Never invent a pace or a time.** The ETA comes from measured history, or it comes with its assumption spelled out, or it is "not yet estimable".
- **Say what you could not check.** Examples: a repo that is not on disk, a task whose state `TaskOutput` could not read, a plan file that has moved. Name each one; do not quietly leave it out of the count.

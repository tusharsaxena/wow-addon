---
description: Sweep the addon for everything still hanging — TODO/FIXME markers, unexecuted audit and review plan items, doc open questions, stale CHANGELOG entries, existing GitHub issues, and recorded-but-unacted Claude memory — then bucketize by type and severity, interview you one item at a time (every item can be deferred or closed as "will not do"), and implement what you accept. Records every decision as a GitHub issue on the addon's own repo, status carried as a `[status]` title prefix, so deferrals stay quiet and closed items never come back.
argument-hint: [code|docs|issues|memory|<path>]
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion]
---

Find every pending decision, unfinished action, and deferred change in the WoW addon at the cwd; bring each one to the user for a call; implement the calls they make.

`$ARGUMENTS` optionally narrows the sweep to a single source (`code`, `docs`, `issues`, `memory`) or to a path prefix (only items located under that path). Empty means sweep everything.

## The store: GitHub issues on the addon's own repo

There is no local ledger. `docs/pending/LEDGER.md` is **retired** — the durable record of issue-audit decisions is the set of GitHub issues on this addon's repo. Everything else about this command is unchanged; only where the decisions live has moved.

Status is carried as a **title prefix**, exactly `[<Status>] <Title>`:

| Decision | Issue title prefix | GitHub issue state | Re-surfaces? |
|---|---|---|---|
| `done` | `[done]` | closed | No — terminal |
| `wont-do` | `[will-not-do]` | closed | No — terminal |
| `deferred` | `[deferred]` | open | Yes, as a collapsed count |
| `untriaged` | `[untriaged]` | open | Yes — interviewed in full next run |

Three of these are decisions; `untriaged` is the absence of one, which is why it is the only value that gets fully re-interviewed rather than collapsed. Never let an `[untriaged]` issue read as agreement to anything.

**The prefix is the data.** Don't decorate it — no emoji marker in the title, no duplicate status word in the label set, no second copy of the status in the body. The old ledger wrote `🟢 done` because a table column needed to scan visually; a title prefix already reads at a glance and a second encoding is one more thing to drift. Keep the four words exactly as spelled above: `[done]`, `[will-not-do]`, `[deferred]`, `[untriaged]`. Don't add a fifth and don't rename one — a filter that has learned these should never have to re-learn them.

**GitHub API guardrail.** Use the `gh` CLI subcommands — `gh issue list`, `gh issue create`, `gh issue edit`, `gh issue close`, `gh issue comment`, `gh issue view`. Where structured data is needed, use `--json` on those subcommands. **Never use `gh api graphql`** for issue work, and never hand-roll GraphQL queries against `api.github.com/graphql` — reaching for GraphQL first is a real, observed failure that wastes a round trip on a deprecated path before falling back. If a REST call is genuinely unavoidable, use `gh api repos/{owner}/{repo}/issues` — never the GraphQL endpoint. Because status lives in the **title prefix**, listing by status is a title filter over `gh issue list --json number,title,state`, **not** a label query and **not** a GraphQL search.

## Step 0 — Locate the addon, and read the store

Confirm the cwd is a WoW addon: at least one `.toc` file, or a `docs/`+`.lua` layout. If it isn't, say so and stop — this command works on an addon repo, not on an arbitrary directory.

Then preflight the store, because it is now **remote**:

1. `gh auth status` — confirm `gh` is installed and authenticated.
2. `gh repo view --json nameWithOwner` — confirm the cwd repo has a GitHub remote `gh` can resolve.

**If either fails, this command cannot record anything. Say so and stop.** This is a change from earlier behaviour: a missing `gh` used to skip one discovery sweep and cost nothing. It is now **fatal to any run that reconciles or records**, because without `gh` there is no way to read past decisions and no way to write new ones — running anyway would re-interview settled items and then drop every answer on the floor. Tell the user exactly that, tell them to install `gh` and run `gh auth login` (or add a GitHub remote), and stop. Never fall back to writing a local file.

The one exception, offered rather than assumed: the discovery sweeps over **code, docs and memory** don't need `gh` at all, so if the user explicitly wants the analysis anyway, you may run them and print the inventory — clearly stamped **unreconciled**, with the warning that settled items *will* appear in it because the store could not be read, and with nothing recorded and nothing implemented. Offer this; don't default to it. An unreconciled inventory silently mistaken for a reconciled one is worse than no inventory.

Read the whole store:

```
gh issue list --state all --limit 200 --json number,title,state,body,labels,createdAt,updatedAt,url
```

`[done]` and `[will-not-do]` issues are terminal and accumulate forever, so on a mature repo they will eventually crowd out the open `[deferred]`/`[untriaged]` rows a run actually needs. **If the result hits the limit, you have not read the store** — say so rather than proceeding on a truncated view, and re-read in two passes (`--state open` in full, then `--state closed` for hash matching). Silent truncation here reproduces exactly the failure this command exists to prevent: an item that looks new because the record of its decision fell off the end of a list.

If the repo has more than 200 issues, say the read was capped and raise `--limit`; a truncated store silently re-opens settled questions.

Note the current git branch (`git rev-parse --abbrev-ref HEAD`) — Step 3.5 needs it.

### Legacy ledger migration (one time, only if the file exists)

If `docs/pending/LEDGER.md` still exists, this repo predates the move. Migrate it in this run, before Step 1:

- **`deferred` rows migrate** — one open `[deferred]` issue each, body carrying the row's ID, evidence hash, source/location and rationale, plus a line saying it was migrated from the retired ledger. If the row already names an issue number in its `Issue` column, **edit that issue's title to carry the `[deferred]` prefix** instead of filing a second one.
- **`done` and `wont-do` rows do NOT migrate.** They are terminal; nothing will ever query them again, and they survive in git history via the deletion commit.
- **`untriaged` rows do not migrate either** — they are not decisions. The sweep re-discovers those items in Step 1 and they get filed fresh.
- Then `git rm docs/pending/LEDGER.md` (and the `docs/pending/` directory if it is now empty). Don't commit — Hard rules still apply.

Show the migration plan (how many rows of each kind, what will be filed) and get approval before creating anything: filing issues is public and other people get notified.

## Step 1 — Discover

Run all four sweeps (or the one `$ARGUMENTS` selected). Every item you surface must carry:

- a **stable ID** — `<SRC>-<NN>`, where `SRC` is `CODE`, `DOC`, `PLAN`, `GIT`, `ISS`, or `MEM` (e.g. `CODE-03`, `PLAN-01`)
- a **location** — `file:line`, an issue number, or a memory filename
- **verbatim evidence** — the marker comment, the plan row, the issue title. Quote it; don't paraphrase.
- an **evidence hash** — the first 8 chars of `sha1` over the verbatim evidence text. The store matches on this, so a marker whose text changed correctly re-surfaces.
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

- `README.md`, root `CLAUDE.md`, `docs/*.md` — open questions, "not yet", "planned", "TBD", "known issue" phrasing
- `docs/ARCHITECTURE.md` → **Known Limitations** section, every entry
- `CHANGELOG.md` → an `Unreleased` section with content in it
- `TODO.md` if present — every unchecked item

Then the high-value one: **unexecuted plan items.** Find the newest `docs/audits/<YYYY-MM-DD>/05_EXECUTION_PLAN.md` and the newest `docs/reviews/<YYYY-MM-DD>/04_EXECUTION_PLAN.md`. For each step or deviation ID they list, check the current code to see whether it was actually carried out. Report each as executed / not executed / partially executed, **with the evidence you used to decide** — a plan row is only a pending item if the code still shows the pre-remediation state. Carry the original deviation/finding ID into your item's evidence so it stays traceable back to the frozen bundle.

Older audit/review bundles are frozen history; don't re-litigate them. If the newest bundle is older than the newest one you can see in a directory listing, you read the wrong one — sort by date, take the latest.

### 1c. The issue store, and git

The issues you read in Step 0 are **not a discovery sweep** — they are the store. Split them in two by their title:

- **Issue carries a `[status]` prefix** → a *known item*. It is this command's own record of a past decision. It does not become a new `ISS-NN` item; it goes straight into Step 2's reconciliation, matched to a freshly-discovered item by the ID and evidence hash in its body.
- **Issue carries no prefix** → an *externally-filed item*. Somebody filed it by hand, or `/wow-addon:add-issue` did. It is real pending work nobody has put to the user through this command, so treat it as **`[untriaged]`**: give it an `ISS-NN` item ID, evidence = the verbatim issue title (plus the body's first meaningful line if the title is thin), location = the issue number, and interview it in full. Closed unprefixed issues are history — skip them.

**What replaces the old dedup rule.** Under the ledger there were two stores, so the same work could exist as a ledger row *and* as an `ISS` item, and Step 2 had to notice and drop one. There is now **one store**, and the rule that keeps it single is: *a prefixed issue is never re-discovered as a new item.* Do not re-implement the old "check whether the issue number appears in the ledger's `Issue` column" reconciliation — there is no such column and no second record to reconcile against. The only remaining duplication risk runs the other way: when you are about to **file** an issue for a discovered item, first check whether an unprefixed issue in the store already describes that same work. If one does, **adopt it** — prefix its existing title rather than filing a second issue, and say so.

Also sweep git itself:

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
- `Deferred` — explicitly postponed at some earlier point (by a `[deferred]` issue, a comment saying so, or a plan row marked deferred)

**Severity**, each asserted with a one-line justification so the ranking is arguable rather than decorative:
- `Critical` — taint, combat-lockdown breakage, saved-variable corruption or data loss, an error thrown on a common path
- `High` — a user-visible defect, or a deviation from the Ka0s WoW Addon Standard carried over from an audit bundle
- `Medium` — maintainability: a stub that callers depend on, drift between code and docs, a dead code path
- `Low` — polish, naming, cosmetic, speculative-future notes

**Store reconciliation.** For each discovered item, look for an issue whose title carries a `[status]` prefix and whose body records the same ID *and* the same evidence hash:

- match found, prefix `[done]` or `[will-not-do]` (both closed) → **drop it entirely.** It is closed. Don't list it, don't count it, don't mention it in the report. These two are terminal: the work happened, or the user decided it never will. Either way it is no longer pending and must not surface again.
- match found, prefix `[deferred]` (open) → file under **Previously deferred**; don't interview it. Deferral is *not* terminal — it's a "not now", so it stays visible as a collapsed count.
- match found, prefix `[untriaged]` (open) → **interview it in full, as if new.** Nobody has ever been asked about this item; the issue only records that it was seen. Don't collapse it, don't count it as previously deferred, and don't let its age imply it was considered and passed over.
- ID matches but hash differs → the item changed since the decision, including if that decision was `[done]` or `[will-not-do]`. Interview it, and say in the question that it was previously decided, what the decision was, and that the evidence has since changed. Reuse the same issue; don't file a second one.
- no match → new item, interview it.

**The hash is the identity; the ID is only a label for this run.** `<SRC>-<NN>` is a sequence number assigned during discovery, so which marker is `CODE-03` shifts the moment a marker is added or removed above it. Match on the **evidence hash first** and treat the ID as a display convenience. An ID that matches with a *different* hash is therefore not evidence that the item changed — far more often it is a different item that inherited the number, and treating it as the same one would reopen and retitle a settled `[will-not-do]` issue for unrelated work. So on an ID-match-hash-mismatch, only treat it as the same item when the issue body's recorded **location and source** also line up; otherwise it is a new item and gets a new issue. When in doubt, file new — a duplicate is recoverable, silently overwriting somebody's settled decision is not.

The distinction that matters: **`deferred` keeps an item alive and quiet; `wont-do` kills it.** If a user has to keep re-declining the same thing, the command is broken.

Prefixed issues with **no** matching discovered item are not automatically stale — the evidence may simply live somewhere this run didn't sweep (`$ARGUMENTS` narrowed it, the file moved). Leave them exactly as they are. Never bulk-close issues because a sweep didn't find their evidence.

Print the inventory as a table grouped by severity (Critical first), showing ID, type, location, and a one-line summary — plus a collapsed count line for **Previously deferred**. Do not print the full evidence for every item here; that's noise. Print evidence when you interview the item.

If the sweep found nothing, say so plainly and stop. That's a good outcome, not a failed run.

## Step 2.5 — Interview now, or just the inventory?

With the inventory on screen, ask once — plainly, not as an `AskUserQuestion` ceremony:

> "N items found. Want to go through them now, or take the inventory and stop here?"

The analysis has value on its own. Someone running this to see where a project stands is not necessarily ready to spend twenty decisions on it, and a command that forces the interview to get the list trains people not to run it.

- **Yes, interview** → Step 3 as normal.
- **No, inventory only** → skip Steps 3, 3.5 and 4 entirely. **Change nothing in the addon.** File every uninterviewed item as an open `[untriaged]` issue (Step 5), then print the report (Step 6). Say clearly in the report that no decisions were recorded and nothing was implemented, and that re-running picks up exactly where this left off.

The point of filing `[untriaged]` issues rather than nothing: the store becomes a durable inventory with evidence hashes attached, so the next run can tell what's genuinely new from what was already seen. It is **not** a decision and must never be treated as one.

Because the store is public, say this out loud before taking the inventory-only path: **the inventory will appear as open issues on the repo.** Get a yes.

## Step 3 — Interview

One item at a time, **most severe first**, using `AskUserQuestion`. Never batch. Never summarize a group as "and 12 more like this" and ask for one blanket call — the point of this command is per-item judgment.

For each item, show its verbatim evidence and location, then offer:

- **2–3 concrete resolution options specific to that item.** Not "fix it" / "don't fix it" — say what fixing it means here. For a stub function: implement it / delete it and its callers / leave the stub and document the limitation. For an unexecuted audit deviation: apply the remediation the bundle already designed / apply a different fix you describe / accept the deviation.
- **"Defer"** — always present. A "not now": the item is recorded as an open `[deferred]` issue and reappears as a collapsed line next run. There is exactly one deferral now.
- **"Will not do"** — always present, always last. A permanent close: the item is recorded as a closed `[will-not-do]` issue and is never raised again. Say plainly in the option text that this is permanent, and say what stays behind if they pick it (the TODO comment still sits in the code, the deviation stays in the frozen audit bundle) so the choice is made with eyes open.

The user can always answer free-text instead of picking. If they do, take their answer over your options — the options are a convenience, not a menu the user is confined to.

**Every recorded decision is now public.** The old command had two deferrals — one into a local file, one into a GitHub issue — so a user could keep a "not now" inside their working copy. That private option is gone: the ledger is retired, and *every* decision this command records, including `[untriaged]` inventory rows, becomes an issue on the repo, visible to anyone who can see it and notifying whoever watches it. Say this **once, up front, at the start of the interview** — not buried in an option label, and never left for the user to discover afterwards from a notification. If they aren't comfortable with that, the honest answer is to stop the interview, not to quietly keep a decision out of the store.

### Filing and updating issues

Every decision writes to the store in Step 5. Two rules apply while interviewing:

1. **Check for an existing issue first.** You already read the whole store in Step 0. If an unprefixed issue clearly covers this item, **don't file a duplicate** — adopt it (Step 5 prefixes its title) and say so. Filing a second issue for the same thing is worse than filing none.
2. **Show the draft before anything is created.** Title and body, the same way `/wow-addon:add-issue` does — an issue is public and other people get notified. For a batch of decisions, one consolidated draft review before Step 5 writes them is fine; silently creating is not.

If a `gh` write fails partway through, the decisions still stand: report exactly which items were written and which weren't, and say that re-running re-offers the unwritten ones. Losing a decision because a network call failed would be the worse outcome — but so would pretending it was recorded.

**Write idempotently, because a timeout is not a failure.** `gh issue create` can create the issue and *then* time out, so a naive retry files a duplicate — the one outcome rule 1 above calls worse than filing none. Before creating any issue, search the store for its evidence hash (`gh issue list --state all --search "<hash>"`, or match against the store you already read in Step 0); if an issue carrying that hash exists, edit it instead of creating a second one. The evidence hash in the body is what makes this safe, so it is written on every issue this command creates, without exception.

**Space the writes out.** A run recording twenty decisions is twenty content-creating API calls; GitHub's secondary rate limits throttle bursts, and being throttled mid-run is precisely how a store ends up half-written. Leave a short gap between mutations and prefer a slow complete run to a fast partial one.

### Follow-through on "will not do"

The closed `[will-not-do]` issue alone is enough to stop the item re-surfacing, so **no further action is required** and none is taken by default. But a dead marker left in the code is a trap for the next reader, so where there's an obvious tidy-up, offer it as a single yes/no follow-up:

- **code marker** → remove the `TODO`/`FIXME`, or rewrite it as a statement of intent (`-- Deliberately not handled: <reason>`). Prefer rewriting over deleting when the comment explains a real constraint.
- **doc entry** (Known Limitations, `Unreleased`, `TODO.md`) → leave it if it documents a genuine limitation; remove it if it only tracked intent to change.
- **a related issue somebody else filed** → offer to close it with a comment explaining the decision. **Requires explicit confirmation** — closing someone's issue is outward-facing and visible to others. Default is no.

Never bundle these into the main decision. Ask separately, accept a plain no, and record the answer in the issue body's rationale.

### Stopping early

If the user says to stop interviewing partway through, the un-interviewed items are recorded as open **`[untriaged]`** issues — never `[will-not-do]`, never `[deferred]`. They weren't declined or postponed; they were never asked, so they come back in full next run. Silence is not a decision, and it is certainly not consent to publish a *decision* — the `[untriaged]` issue records only that the item was seen, and its body must say so in those words.

**Ask before filing them.** Stopping the interview is not permission to publish the remainder:

> "Stopping here. The N items you weren't asked about would be filed as open `[untriaged]` issues so the next run knows they were seen. File them, or leave them unrecorded?"

Both answers are legitimate and neither is a decision about the items themselves. If the user declines, file nothing, say in the report that the remainder is unrecorded, and note that the next run rediscovers them from source — the sweeps are repeatable, so nothing is lost by not filing. This is the same consent gate the inventory-only path takes above, for exactly the same reason: an item the user never saw must not become a public artifact on their repo because they ran out of time. Then go to Step 4 with the answers you did get.

## Step 3.5 — Branch decision

Before touching a single file, count the accepted items. If **five or more** were accepted, **or any accepted item is Critical**, and the current branch is `master` or `main`, propose a working branch:

> "That's N accepted items on `master`. Want me to branch first? Suggested: `pending/<YYYY-MM-DD>`."

Ask; don't just do it. If the user declines, or the set is small, or you're already on a non-default branch, proceed on the current branch.

## Step 4 — Implement

Only the accepted items. Group the work by file so each file is touched once.

- Use `Edit` for surgical changes; `Write` only when a file is being created or fully replaced.
- **Write the DECLARED line ending, not the observed one.** Ask git what the repo declares for the file — `git check-attr eol -- <path>` — and write that: CRLF in a client-bound repo, LF in one that ships nothing to the WoW client (`line-endings-§2`). A file whose endings disagree with the declaration is a **straggler**, so preserving what you find propagates the defect rather than respecting a local convention. Where nothing is declared, preserve what is there.
- When an accepted item's resolution is "implement per the audit bundle", follow the remediation the bundle's `04_TECHNICAL_DESIGN.md` already specified rather than inventing a new one.
- If an item turns out to be un-implementable once you're in the code (the premise was wrong, it's already done, it conflicts with another accepted item), **stop on that item and tell the user** — don't improvise a different change.

When the edits are in, run the test battery if the addon has one — luacheck, the headless `tests/` harness, a Makefile `test` target. Report the result. If something you changed broke a test, fix it or revert that item and say which.

## Step 5 — Write the issues

Bring the store in line with the decisions. Each item ends up as exactly **one** issue whose title prefix and GitHub state match its decision, per the mapping table at the top.

**Which `gh` call, per case:**

| Case | Call |
|---|---|
| New item, any decision | `gh issue create --title "[<status>] <Title>" --body "$(cat <<'EOF' … EOF)"` — then `gh issue close` if the status is `done` or `will-not-do` |
| Existing prefixed issue, status changed | `gh issue edit <n> --title "[<new>] <Title>"`, plus `gh issue close <n>` / `gh issue reopen <n>` so state matches |
| Unprefixed issue adopted for a discovered item | `gh issue edit <n> --title "[<status>] <existing title>"` and `gh issue comment <n>` with the evidence block — keep the original title text; you are prefixing it, not rewriting somebody's words |
| Decision unchanged (e.g. still deferred) | Leave it alone. Don't churn the issue, don't re-comment, don't touch `updatedAt` |

Prefix and state must never disagree. `[done]` and `[will-not-do]` are **closed**; `[deferred]` and `[untriaged]` are **open**. An open `[done]` issue is a bug in this command — if you find one, fix the state and say so in the report.

**Issue body**, for anything this command files or adopts. Keep it stable and machine-readable, because the next run parses it:

```
### Pending-audit record

- **Item ID:** CODE-03
- **Evidence hash:** 1a2b3c4d
- **Source:** code marker
- **Location:** Modules/Aura.lua:212
- **Severity:** Medium — a stub two callers already depend on
- **Decided:** 2026-08-06

### Evidence

> -- TODO: handle the pet-swap case before 11.2

### Rationale

<the user's reason, in their words>
```

- **Item ID and evidence hash are mandatory** — they are the whole matching key for Step 2. An issue missing them cannot be reconciled and will cause the item to be re-interviewed.
- **Rationale** is the user's reason in one line, in their words where they gave them. For `[untriaged]` there is no reason to give: write why it wasn't asked (`inventory-only run`, `interview stopped early`) so the issue can't be misread as a considered judgment. For `[will-not-do]` the rationale is **the most valuable field in the store** — it's what stops a future reader (or a future agent) from re-opening a settled question. Never leave it blank; if the user gave no reason, write what you understood their reason to be and mark it as inferred.
- Labels are optional and orthogonal (`bug`, `enhancement` as `/wow-addon:add-issue` uses them). **Status is never a label** — the prefix is the status.

The two closed states are load-bearing. Getting an issue's status wrong means either losing real work (`[will-not-do]` on something the user wanted) or nagging them forever (`[deferred]` on something they closed). If you're unsure which the user meant, ask rather than guess.

## Step 6 — Report

Print:

- **Implemented** — item ID, what changed, files touched, and the issue number now carrying `[done]`
- **Will not do** — item ID and reason, the closed `[will-not-do]` issue number, plus any follow-through taken (marker rewritten, another issue closed). Show these once, here, so the user can see what they just closed permanently — then never again.
- **Deferred** — item ID, one-line reason, and the open `[deferred]` issue number and URL. Where an existing issue was adopted rather than a new one filed, say so.
- **Untriaged** — count, the severity spread (e.g. "2 Critical, 5 Medium"), and the issue numbers filed. On the inventory-only path this is the whole report, so make it useful: state plainly that no decisions were recorded, nothing was implemented, and re-running resumes from here.
- **Previously deferred** — count only, with the issue numbers
- **Went public this run** — every issue created, edited, or closed, with its URL. The store is public; the user should be able to see the full outward-facing footprint of the run in one place.
- **Skipped sweeps** — any source that couldn't run (no memory dir, no audit bundle) and why. `gh` is not on this list — without it the command stopped at Step 0.
- **Blocked** — anything accepted but not implementable, with what stopped you; and any `gh` write that failed
- Test results, if a battery ran
- A reminder to review the diff before committing

## Hard rules

- **Use the `gh` CLI subcommands for all issue work** — `gh issue list`, `gh issue create`, `gh issue edit`, `gh issue close`, `gh issue comment`, `gh issue view`, with `--json` where structured data is needed. **Never use `gh api graphql`**, and never hand-roll GraphQL against `api.github.com/graphql`. If a REST call is genuinely unavoidable, use `gh api repos/{owner}/{repo}/issues` — never the GraphQL endpoint. Listing by status is a **title-prefix filter** over `gh issue list --json number,title,state`, not a label query and not a search.
- **Don't write a local ledger.** `docs/pending/LEDGER.md` is retired. Don't create it, don't recreate it as a cache, don't mirror the store into the repo.
- **Don't commit.** Committing is `/wow-addon:commit`'s job.
- **Don't bump the version.** That's `/wow-addon:bump-version`'s job, even if an accepted item is about the version.
- **Don't act on an item the user didn't accept.** Deferring and "will not do" are real answers; both leave the code untouched unless the user separately opted into a follow-through tidy-up.
- **Don't resurrect closed items.** A `[done]` or `[will-not-do]` issue with a matching evidence hash means the question is settled. Don't surface it, don't count it, don't "just check in" about it. The only thing that re-opens it is the evidence itself changing.
- **Don't infer "will not do" from silence.** Only a user explicitly choosing it makes an item `[will-not-do]`. An early stop, a skipped question, or an ambiguous answer is `[untriaged]` or `[deferred]`, never a permanent close.
- **Don't file an issue for work the user hasn't seen.** Every issue this command creates traces to an item that was either interviewed or explicitly recorded as `[untriaged]` with the user's yes to the inventory-only path. No speculative filing, no batch drive-by, no consolation issue for an item nobody got to.
- **Don't invent pending items.** Every item traces to verbatim evidence at a real location. If you think something *should* be done but nothing in the repo, docs, issues, or memory says so, that's your opinion — leave it out, or raise it once in the report under a clearly labelled "Not a pending item, but noticed" line.
- **Don't edit frozen artifacts.** `docs/audits/<date>/` and `docs/reviews/<date>/` bundles are history. Implement their unexecuted items in the code; leave the bundles as written.
- **Don't re-interview settled items.** The store exists so a deferral means something.
- **Don't rewrite somebody else's issue.** Adopting an unprefixed issue adds the prefix and a comment; it never rewrites the title text or edits the body they wrote.
- **Don't touch `libs/`** or any vendored library.

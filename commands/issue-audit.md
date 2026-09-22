---
description: Sweep the addon for everything still hanging — TODO/FIXME/stub markers, unexecuted audit and review plan items, doc open questions and Known Limitations, an Unreleased CHANGELOG section, stashes and follow-up commits, and recorded-but-unacted Claude memory — and file anything not already in the issue store as a new GitHub issue labelled `state:untriaged` plus a severity. Discovery only: it never interviews you and never changes code. Triage is `/wow-addon:issue-triage`.
argument-hint: [here|all|<repo>] [code|docs|issues|memory|<path>]
allowed-tools: [Read, Glob, Grep, Bash, AskUserQuestion]
---

Find every pending decision, unfinished action and deferred change in the addon, and make sure each one exists as a GitHub issue. **This command discovers and files. It does not triage.**

That split is the point. Discovery is mechanical and can run unattended over any scope; triage is a conversation that costs you a decision per item. Fusing them meant you could not sweep without committing to an interview, which trained people not to sweep. Everything this command files lands as **`state:untriaged`** — seen, recorded, and explicitly *not* decided. `/wow-addon:issue-triage` is what turns those into decisions.

## The store: GitHub issues on the addon's own repo

There is no local ledger. `docs/pending/LEDGER.md` is **retired** — the durable record is the set of GitHub issues on the addon's repo. Two facts about every issue are carried as **GitHub labels**:

**Status** — exactly one `state:` label per issue:

| Status | Label | Color | GitHub state | Meaning |
|---|---|---|---|---|
| done | `state:done` | green `00ff00` | closed | Implemented. Terminal |
| will-not-do | `state:will-not-do` | blue `0000ff` | closed | Will never be done. Terminal |
| triaged | `state:triaged` | yellow `ffff00` | open | Decided: not now. Still on the books |
| untriaged | `state:untriaged` | red `ff0000` | open | Found, never put to the user. **What this command writes** |

**Severity** — exactly one `severity:` label per issue:

| Severity | Label | Color | Meaning |
|---|---|---|---|
| Critical | `severity:critical` | red `110000` | Taint, combat-lockdown breakage, saved-variable corruption or data loss, an error on a common path |
| High | `severity:high` | orange `110800` | A user-visible defect, or a Ka0s standard deviation carried from an audit bundle |
| Medium | `severity:medium` | yellow `111100` | Maintainability: a stub callers depend on, code/doc drift, a dead path |
| Low | `severity:low` | green `001100` | Polish, naming, cosmetic, speculative-future notes |

**Every issue always carries one of each.** There is no fifth status, no fifth severity, and no unlabelled state. An issue that arrives without one — filed from the GitHub web UI, or by someone who doesn't use these commands — is repaired on sight: see *Stray issues* below.

**The labels are the data.** No `[status]` title prefix, no emoji marker, no severity word in the title, no second copy of either in the body. The old `[untriaged] …` title-prefix convention is **retired**: a stale prefix on an old issue is leftover text, and the label is what to trust. When you meet one, strip it as part of the stray repair.

**GitHub API guardrail.** Use the `gh` CLI subcommands — `gh issue list`, `gh issue create`, `gh issue edit`, `gh issue close`, `gh issue comment`, `gh issue view`, `gh label list`, `gh label create` — with `--json` where structured data is needed. **Never use `gh api graphql`**, and never hand-roll GraphQL against `api.github.com/graphql`: reaching for GraphQL first is a real, observed failure that burns a round trip on a deprecated path before falling back. If REST is genuinely unavoidable, use `gh api repos/{owner}/{repo}/issues` — never the GraphQL endpoint. Listing by status or severity is a plain **`--label` query**, not a title filter and not a search.

**Space out writes.** A sweep that files twenty issues is twenty content-creating API calls, and GitHub throttles bursts. Leave a few seconds between mutations and prefer a slow complete run to a fast partial one. On an `all`-scope run, work **one repo at a time** rather than firing at several at once.

## Step 0 — Resolve the scope

The **first** `$ARGUMENTS` token, if it is a scope keyword:

- **absent, or `here`** → the repo at the cwd. **This is the default.**
- **`all`** → every addon repo in the collection. Read the roster from `WowAddonStandards/standards/ADDONS.md` (folder + repository per row) rather than hardcoding it; if that repo isn't checked out, fall back to sibling directories containing a `.toc` and **say in the report that the roster was inferred**.
- **a repo name** → that repo alone, matched case-insensitively against the roster. If it matches nothing, say so, list the valid names, and stop. Don't guess at a near-miss.

If the cwd is not an addon repo and no scope was given, **ask** which scope to use rather than guessing — sweeping the wrong repo wastes a run, and sweeping `all` when the user meant one repo files issues on ten repos they weren't thinking about.

Any remaining token narrows the sweep to one source (`code`, `docs`, `issues`, `memory`) or to a path prefix. Empty means sweep everything.

For each repo in scope, confirm it is a WoW addon (at least one `.toc`, or a `docs/`+`.lua` layout), then preflight:

1. `gh auth status` — `gh` installed and authenticated.
2. `gh repo view --json nameWithOwner` — the repo has a GitHub remote `gh` can resolve.

**If either fails, this command cannot record anything. Say so and stop.** Without `gh` there is no way to read what is already filed and no way to file anything, so a run would re-report settled items and drop every result. Never fall back to writing a local file.

The one exception, offered rather than assumed: the code, docs and memory sweeps don't need `gh`. If the user explicitly wants the analysis anyway, run them and print the inventory clearly stamped **unreconciled** — with the warning that already-filed items *will* appear because the store could not be read, and with nothing filed. Offer this; don't default to it.

### Ensure the label set exists

Before any write, make sure the eight collection labels exist on the repo. `gh label create --force` creates a missing label and updates an existing one's color and description, so it is safe to run every time and repairs a drifted color on the way:

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

Read `gh label list --limit 100 --json name,color` first and run only the creates that are missing or wrong, so a repo already set up costs one call instead of eight. Report any create that failed; a missing label is a reason to report and file the issue without it, never a reason to lose the finding.

Read the whole store:

```
gh issue list --state all --limit 200 --json number,title,state,body,labels,createdAt,updatedAt,url
```

`state:done` and `state:will-not-do` issues are terminal and accumulate forever, so on a mature repo they will crowd out the open rows a run needs. **If the result hits the limit, you have not read the store** — say so rather than proceeding on a truncated view, and re-read in two passes (`--state open` in full, then `--state closed` for hash matching). Silent truncation reproduces exactly the failure this command exists to prevent: an item that looks new because the record of it fell off the end of a list.

### Stray issues

An issue carrying **no** `state:` label was filed outside these commands, or predates the label scheme. Repair it:

- **open** → `gh issue edit <n> --add-label "state:untriaged"`
- **closed** → `state:done` if it was closed as completed, `state:will-not-do` if closed as not planned (`gh api repos/{owner}/{repo}/issues/<n>` reports `state_reason`)

An issue carrying no `severity:` label gets one too — assess it from its body against the ladder above and add it, recording the one-line justification in the report so the call is arguable.

**A legacy `[status]` title prefix is stripped as part of the same repair.** Set the label from the prefix, then `gh issue edit <n> --title "<title with the prefix removed>"`. Keep the rest of the title text exactly — you are removing a prefix, not rewriting somebody's words. If the label and a leftover prefix disagree, the **label wins**; report the disagreement rather than silently picking one.

**Report every repair** in Step 4 — labels added, prefix stripped, old and new title — so a title changing under someone is never a silent event. After repair the issue is an ordinary `state:untriaged` item and `/wow-addon:issue-triage` will pick it up.

## Step 1 — Discover

Run all four sweeps (or the one the argument selected). Every item you surface must carry:

- a **stable ID** — `<SRC>-<NN>`, where `SRC` is `CODE`, `DOC`, `PLAN`, `GIT` or `MEM`
- a **location** — `file:line`, or a memory filename
- **verbatim evidence** — the marker comment, the plan row. Quote it; don't paraphrase.
- an **evidence hash** — first 8 chars of `sha1` over the verbatim evidence text. The store matches on this, so a marker whose text changed correctly re-surfaces as new.
- **age**, where knowable — `git blame -L <line>,<line> -- <file>` on a code marker. An item sitting for a year is different information from one added yesterday.

### 1a. Code markers

Grep the addon's own `.lua` and `.xml` files — **exclude `libs/`, `Libs/` and any vendored library directory**:

- `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `NOTE:` followed by deferral language
- prose deferrals in comments: `for now`, `temporary`, `revisit`, `later`, `placeholder`, `stub`, `not implemented`, `come back to`, `once we`
- **stub functions** — a body that is empty, only a comment, or only `return` / `return nil`
- **commented-out blocks** — three or more consecutive commented lines that parse as Lua rather than prose
- **hardcoded values flagged as provisional** — a literal whose comment matches the deferral vocabulary above

Read enough surrounding lines to state what the marker actually asks for. A bare `-- TODO` with no context is itself a finding ("marker with no stated intent").

### 1b. Docs and frozen artifacts

- `README.md`, root `CLAUDE.md`, `docs/*.md` — open questions, "not yet", "planned", "TBD", "known issue"
- `docs/ARCHITECTURE.md` → **Known Limitations**, every entry
- `CHANGELOG.md` → an `Unreleased` section with content in it
- `TODO.md` if present — every unchecked item

Then the high-value one: **unexecuted plan items.** Find the newest `docs/audits/<YYYY-MM-DD>/05_EXECUTION_PLAN.md` and the newest `docs/reviews/<YYYY-MM-DD>/04_EXECUTION_PLAN.md`. For each step or deviation ID, check the current code to see whether it was carried out. Report executed / not executed / partially executed **with the evidence you used to decide** — a plan row is a pending item only if the code still shows the pre-remediation state. Carry the original deviation ID into the evidence so it stays traceable to the frozen bundle.

Older bundles are frozen history; don't re-litigate them. Sort by date and take the latest.

### 1c. Git

- `git stash list` — each stash is unfinished work
- `git status --porcelain` — uncommitted changes
- `git log --oneline -50` — subjects/bodies containing `follow-up`, `followup`, `temporary`, `revert later`, `part 1`, `WIP`, `first pass`

The issues read in Step 0 are **not** a discovery sweep — they are the store, and they are what Step 2 reconciles against.

### 1d. Claude memory

Look under `~/.claude/projects/<cwd-path-slug>/memory/` (the slug is the absolute cwd with `/` replaced by `-`). Read `MEMORY.md` and the entries it indexes. Surface entries recording a decision, constraint or user instruction **with no corresponding change in the code or docs**.

Memory reflects what was true when written. Before surfacing one, verify the file, function or flag it names still exists.

## Step 2 — Reconcile against the store

For each discovered item, look for an issue whose body records the same **evidence hash**:

- **match, `state:done` or `state:will-not-do`** (closed) → **drop it entirely.** Terminal. Don't list it, don't count it, don't file anything.
- **match, `state:triaged`** (open) → already on the books. Don't file a duplicate; count it under *Already tracked*.
- **match, `state:untriaged`** (open) → already filed and awaiting triage. Don't file a duplicate; count it under *Already tracked*.
- **hash matches nothing** → **new.** This is what the command files.

**The hash is the identity; the ID is only a label for this run.** `<SRC>-<NN>` is a sequence number, so which marker is `CODE-03` shifts the moment one is added above it. Match on the hash and treat the ID as display. An ID that matches with a *different* hash is far more often a different item that inherited the number than the same item changed — so treat it as the same item only when the issue body's recorded **location and source** also line up. When in doubt, file new: a duplicate is recoverable, silently overwriting a settled decision is not.

Before filing, check whether an existing issue already describes the same work in different words. If one does, **adopt it** rather than filing a second — and say so.

Labelled issues with **no** matching discovered item are not stale. The evidence may live somewhere this run didn't sweep. Leave them alone; **never bulk-close issues because a sweep didn't find their evidence.**

Classify each new item by **severity** against the ladder in the store table above, each with a one-line justification so the ranking is arguable. The severity becomes the issue's `severity:` label, and it is what `/wow-addon:issue-triage` orders its queue by — a wrong severity does not just mislabel an item, it puts it in front of or behind the wrong things when somebody sits down to decide.

Print the inventory grouped by severity (Critical first) showing ID, location and a one-line summary, plus counts for *Already tracked* and *Dropped as terminal*.

If nothing new was found, say so plainly and stop. That is a good outcome, not a failed run.

## Step 3 — File the new items as `state:untriaged`

**Show the list and get approval before creating anything.** Filing is public and other people get notified. Show the count, the titles and the severities, then ask once. On a `all`-scope run, show it per repo — twelve issues across one repo and twelve across eight are different decisions.

Then, one issue per new item:

```
gh issue create --title "<Title>" \
  --label "state:untriaged" --label "severity:medium" \
  --body "$(cat <<'EOF'
### Issue-audit record

- **Item ID:** CODE-03
- **Evidence hash:** 1a2b3c4d
- **Source:** code marker
- **Location:** modules/Aura.lua:212
- **Severity rationale:** a stub two callers already depend on
- **Found:** 2026-08-06

### Evidence

> -- TODO: handle the pet-swap case before 11.2

### Status

Untriaged — found by a sweep and recorded. **Nobody has been asked about this yet**, and this issue is not agreement to do it. `/wow-addon:issue-triage` puts it to a human.
EOF
)"
```

- **Item ID and evidence hash are mandatory.** They are the whole matching key for the next run's Step 2. An issue missing them cannot be reconciled and will be re-filed as a duplicate forever.
- **Both labels are mandatory.** `state:untriaged` and one `severity:` label go on at creation, in the same call — an issue created bare and labelled afterwards is one failed call away from being invisible to every status query in the family.
- **The body records the severity *rationale*, not the severity.** The level itself lives in the label; writing it in the body too creates a second copy that drifts the first time triage or a later sweep revises it.
- **Title** is a crisp statement of the work, derived from the evidence, with **no status prefix and no severity word**. Don't paste a raw `TODO` as a title, and don't invent scope the evidence doesn't support.
- **Write idempotently.** `gh issue create` can create the issue and *then* time out, so a naive retry files a duplicate. Before creating, search the store for the evidence hash; if an issue carries it, edit rather than create.
- **Never file with any status but `state:untriaged`.** This command has no way to know whether something should be done — it hasn't asked. A sweep that files `state:triaged` is asserting a decision nobody made.
- Tag labels (`bug`, `enhancement`) are optional and orthogonal to both.

## Step 4 — Report

- **Filed** — every new issue: item ID, severity, title, number and URL
- **Already tracked** — count, split `state:untriaged` / `state:triaged`, with numbers
- **Dropped as terminal** — count only; these are settled and are not listed
- **Stray issues repaired** — every issue that gained a `state:` or `severity:` label or lost a legacy title prefix, with its old and new title and the labels added. Never silent.
- **Skipped sweeps** — any source that couldn't run and why
- **Failed writes** — any `gh` call that failed, and which item it was for
- The count of `state:untriaged` issues now open, their severity split, and a pointer: `/wow-addon:issue-triage` to decide them

## Hard rules

- **Discovery only. Never triage.** Don't interview, don't ask the user to decide an item's fate, don't file anything as `state:triaged`, `state:done` or `state:will-not-do` on the strength of your own reading. The whole value of the split is that a sweep is cheap and safe to run.
- **Never change code.** No `Edit`, no `Write`, no fixing the `TODO` you just found. This command reads the repo and writes GitHub. If a marker is trivially fixable, say so in the report and leave it.
- **Don't commit, don't bump the version, don't touch `libs/`.**
- **Every issue this command creates or repairs ends up with exactly one `state:` label and exactly one `severity:` label.** Two of either is a defect; report it rather than picking one at random.
- **Never put status or severity in the title.** No `[untriaged]` prefix, no emoji marker, no severity word. Strip a legacy prefix when you meet one, and say you did.
- **Use the `gh` CLI subcommands.** Never `gh api graphql`.
- **Don't file an issue for something you can't point at.** Every item traces to verbatim evidence at a real location. If you think something *should* be done but nothing in the repo says so, that's your opinion — put it in the report under "Not a pending item, but noticed", never in the store.
- **Don't rewrite somebody else's issue.** Repairing a stray adds the missing labels and removes a legacy prefix — nothing else.
- **Don't edit frozen artifacts.** `docs/audits/<date>/` and `docs/reviews/<date>/` are history.
- **Don't resurrect closed items.** A terminal issue with a matching evidence hash means the question is settled; only the evidence changing re-opens it.

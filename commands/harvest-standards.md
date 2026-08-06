---
description: Harvest learnings from the whole Ka0s collection — every addon repo plus LibKa0s — and promote what has earned it into the Ka0s WoW Addon Standard. Reads code, audit and review bundles, each repo's issue-audit issue store, Compat modules and per-addon quirk files; dedups against the standard's own open-evolutions list; writes a frozen harvests/<date>/ bundle, interviews you per proposal, and applies the accepted ones with the full ripple (section, index blurb, anti-pattern range, changelog, version bump, context pack, playbooks). Runs in the WowAddonStandards repo; read-only on every addon repo.
argument-hint: [repo names | quirks | deviations | decisions | patterns | all]
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion]
---

Harvest what the Ka0s collection has **learned** since the standard last moved, and promote the findings that have earned it into the **Ka0s WoW Addon Standard**. Run this from inside the `WowAddonStandards` repo. `$ARGUMENTS` may narrow the sweep to named repos or to one category (`quirks`, `deviations`, `decisions`, `patterns`); empty means the full sweep. (`ledgers` is accepted as a legacy alias for `decisions`.)

## Direction of travel

This is the **upstream** half of a two-command cycle, and the mirror image of `/wow-addon:revendor-standards`:

- **`/wow-addon:revendor-standards`** runs in an addon repo and carries the standard **down** into it.
- **This command** runs in the standards repo and carries the collection's learnings **up** into the standard.

The reason the pair exists is that knowledge in this collection is discovered **per repo** and paid for **per repo**. One addon fights the client for an afternoon, writes down what it found, and the other eight rediscover it later at full price — or worse, never do, and ship the bug the first one already fixed. The standard is the only place a finding stops being paid for twice. Nothing else in the toolkit reads across repos: `standards-audit` measures one addon, `review` reviews one addon, `issue-audit` triages one addon. **Cross-repo synthesis is this command's entire reason to exist**, so a run that only re-reads one repo has done nothing the existing commands did not already do.

## Absolute rule — read-only on every addon repo

**Never write to an addon repo. Not one byte.** Not a fix, not a doc, not a `midnight-quirks.md` entry, not a tidy-up of a file you are reading. Your only writes are inside the `WowAddonStandards` repo.

This is not a safety nicety, it is what makes the harvest trustworthy. You are about to read N repos' worth of evidence and argue from it; if you also edit as you go, the evidence stops being independent of the argument, and the next run reads your own edits back as if they were nine repos agreeing. Downstream adoption is a **separate, per-repo, user-initiated** act (`/wow-addon:standards-audit`, then `/wow-addon:revendor-standards`) — you name the debt at the end and stop there.

The corollary: **never edit a frozen `docs/audits/<date>/` or `docs/reviews/<date>/` bundle**, in any repo, for any reason. Those are the harvest's primary source. A bundle records what was true on its date against the standard of its date; that is exactly what makes it evidence.

## Step 0 — Confirm where you are, and resolve the standard

1. Confirm cwd is the `WowAddonStandards` repo (it has `standards/STANDARDS.md`, `AUDIT.md`, `NEW_ADDON.md` at the expected paths). If it is not, **stop** and say so — this command writes to the standard, and running it from an addon repo would either write nothing useful or write into the wrong tree.
2. Read the standard **from the working tree**, not from raw GitHub. This is the one spec in the plugin that reads local files rather than fetching: you are about to *edit* these files, so you must measure against the working copy, including any uncommitted change. Read `standards/STANDARDS.md` and **every section file its Sections list links** — follow the list, never hard-code a section filename. Note the current version and date.
3. Read `standards/standards/open-evolutions.md` (via the Sections list, not by path assumption). This is the standard's own ledger of "considered, not yet done", and it is the dedup key for the whole run.
4. Read `standards/ADDONS.md` — the roster.

## Step 1 — Establish the collection

Build the repo list from two sources and reconcile them:

- The **roster** in `standards/ADDONS.md`.
- The **siblings on disk** — directories next to the standards repo containing a root `.toc` (an addon) or identifying as `LibKa0s`.

Report the drift both ways, because each direction means something different: a repo **on disk but unrostered** is invisible to every roster-driven process and its learnings have never been harvested; a repo **rostered but absent** means this machine cannot see it, so every "N repos do X" count in this run is measured against a smaller collection than the standard thinks it has. Say which repos you actually read, and read the count claims in your own output against that list.

`LibKa0s` is in scope and is **not** an addon — it is the shared library, so it contributes differently (see category 8). Reading a sibling repo is exactly what this command does; the read-only rule forbids writing to them, not reading them.

## Step 2 — Harvest, with evidence

Sweep the categories below. **Every finding carries `repo:file:line`** — a claim without a citation cannot become a rule, because a rule the collection cannot trace back to its evidence is one nobody can argue with later when it turns out to be wrong.

### 1. Convergent patterns — the same solution, independently

Three or more repos solving the same problem the same way, with the standard **silent** on it, is a convention the collection has already adopted; the standard is merely late. Codify it as the rule it already is.

### 2. Divergent patterns — the same problem, N different ways

The higher-value half of the same sweep. When repos solve one problem several ways, one of two things is true, and they lead to different places: either the standard should **pick** one (a rule), or the thing is substantial enough that every repo writing its own is the waste, and it belongs in **`LibKa0s`** as a module (an extraction candidate). The five-major LibKa0s extraction came from exactly this observation, so it is a proven shape — but note that an extraction proposal is a **library** change with a standard change trailing it, and it must be labelled that way rather than filed as a rule.

### 3. Midnight quirks — client behavior discovered the hard way

Read every addon's own quirks file and its `Compat` module, plus CHANGELOG entries and code comments describing a client behavior worked around. Look for the **same quirk written up more than once**: independent discoveries of one behavior are the clearest possible evidence that the finding belongs upstream, and the versions will differ in depth — one repo will have probed further than the others. **Promote the deepest version, and say which repo it came from**; a merge that averages three write-ups down to their common denominator throws away precisely the part that cost someone an afternoon.

Quirks land upstream in the standard's **quirks catalogue section** and are then vendored back into every addon by `/wow-addon:revendor-standards`. Find that section through the Sections list. If no such section exists yet, **proposing it is itself a valid harvest proposal** — go through the normal interview and the normal ripple, do not create a section unasked.

### 4. The audit and review corpus

Every `docs/audits/<date>/02_DEVIATIONS.md` and `docs/reviews/<date>/01_FINDINGS.md` in the collection. Two patterns matter, and they say opposite things:

- **One deviation ID recurring across dates within one repo** — the fix never sticks. That is rarely an addon problem; it usually means the rule has no teeth, no tooling, or no clear fix direction.
- **The same deviation across many repos** — a standards gap, not N addon bugs. If most of the collection fails the same rule the same way, the rule is unclear, unenforceable, or wrong, and filing N tickets treats the symptom.

### 5. Standard-internal contradictions

An audit that has to **punt to the user** because two sections disagree has found a defect in the standard that no per-addon process will ever fix — the auditor cannot resolve it, and the addon author resolves it locally and privately, differently each time. Grep the bundles for exactly this shape: a deviation citing two sections in tension, or fix directions that say the choice is the user's. These are the highest-value findings in the corpus and the easiest to miss, because each one is filed as a single addon's edge case.

### 6. `[will-not-do]` issues — accepted deviations the standard never heard about

`documentation-§6` requires an addon to **record** an accepted deviation, and `issue-audit` has been doing exactly that — but recording it in the addon tells the standard nothing. That record used to live in `docs/pending/LEDGER.md`; it now lives in **GitHub issues on each addon's own repo**, with status carried as a title prefix (`[done]`, `[will-not-do]`, `[triaged]`, `[untriaged]`). The ledger is retired. **This harvest category must not die with it** — it is the only channel through which a collectively-refused rule reaches the standard.

For every repo in the sweep, read both halves of the store:

```
gh issue list --repo <owner>/<repo> --state closed --limit 200 --json number,title,body,url   # keep titles starting "[will-not-do]"
gh issue list --repo <owner>/<repo> --state open   --limit 200 --json number,title,body,url   # keep titles starting "[triaged]"
```

Filter on the **title prefix** in the result you get back. Do not use a label query and do not use a search API. The rationale you want is in the issue body under `### Rationale`, and the `filename-§N` rule it refuses is usually in the evidence block above it.

A `[will-not-do]` is a considered, argued refusal with a rationale attached; the **same** refusal in three repos is not three addons being stubborn, it is a rule the collection has collectively declined to follow, and the standard should either change or state why it holds. Harvest `[triaged]` issues too, more weakly: the same item triaged-but-not-done in every repo is a rule too expensive to satisfy, which is its own finding.

Cite the issue URL as the evidence for each proposal, the way a ledger row used to be cited. If a repo still has a `docs/pending/LEDGER.md`, it has not migrated yet — read it as well for this run, note it in the bundle as un-migrated, and don't let its rows go unharvested.

**GitHub API guardrail.** Use the `gh` CLI subcommands — `gh issue list`, `gh issue view` — with `--json` for structured data. **Never use `gh api graphql`** for issue work, and never hand-roll GraphQL queries against `api.github.com/graphql`; reaching for GraphQL first is a real, observed failure that wastes a round trip on a deprecated path before falling back. If a REST call is genuinely unavoidable, use `gh api repos/{owner}/{repo}/issues` — never the GraphQL endpoint. This command is **read-only on every addon repo**, so `gh issue list` and `gh issue view` are the only issue calls it may make at all.

### 7. Rules nobody satisfies, and rules nobody needs

- A **MUST that N repos fail** reads two ways — the collection is non-compliant, or the rule is wrong. **Never pick.** Present both readings with the counts and let the user decide; guessing here is how a real rule gets softened away, or how eight repos get told to do busywork.
- The inverse, offered more tentatively: a rule that **every repo satisfies trivially and no audit has ever cited** may be dead weight. Propose retirement as a question, never as a cleanup — a rule can be uncited precisely *because* it works, and deleting it is how the behavior comes back.

### 8. LibKa0s ↔ standard drift

The library moves faster than the prose describing it. Compare what `LibKa0s` actually ships — majors, modules, the members each exposes, the degradation-stub contract — against what the relevant sections claim. A shipped major the standard does not describe is a gap; a described member the library no longer has is worse, because addons are being told to call it.

Also read **why** any consumer's vendored copy drifted. Downstream that is an anti-pattern #45 finding and gets reverted, but the *cause* is a signal: someone needed something the library did not offer, and the correct fix is an **additive** field upstream. A drift that keeps recurring in the same place is a missing feature wearing a violation's clothes.

### 9. Undocumented emergent conventions

Structures most of the collection has adopted while the standard stayed silent — extra `docs/` files, directory shapes, file-naming habits, comment conventions. Consensus plus silence needs a **decision**: codify it or forbid it. Leaving it undecided is the state that produces divergent copies, because each new addon guesses, and half of them guess differently.

### 10. Tooling gaps — findings whose fix is not prose

Some recurring deviations recur because **nothing checks them**. The right output is then a `.luacheckrc` rule, a mechanical check added to `AUDIT.md`, or a test the kit should carry — not another paragraph in a section that the last paragraph already covered. Allow this outcome explicitly. A standard that answers every finding with more prose grows in the one dimension that does not help: a rule nobody can check is a rule that degrades to a suggestion, and the collection already demonstrates which rules those are.

## Step 3 — Filter before proposing

Three filters, in order. Each one exists because skipping it produces a specific, observed failure.

1. **Date filter.** Every audit bundle records the standard version it was measured against. Resolve each finding against **today's** standard before believing it: a deviation against a rule that has since changed, or a place in a rule that has since been deleted, is settled history. Without this filter the harvest confidently re-proposes what the standard already fixed, and the evidence looks strong precisely because the old rule was failed by everyone before it was fixed.
2. **`open-evolutions.md` dedup.** A finding already recorded there is **not a new item — it is a vote**. Record it as increased evidence for that existing entry (with the new citations) and carry it into the interview as a strengthened case. Opening a duplicate loses the fact that this was already considered, and loses whatever reasoning deferred it.
3. **Evidence bar.** No proposal without `repo:file:line` from **at least two repos**, or **one repo plus an explicit stated cost** — a real consequence, measured or observed, not "this seems better". Everything below the bar goes to a **watch list** in the bundle, where the next run will find it and where a second repo's evidence promotes it. One repo's habit is not the collection's convention, and the standard is not the place to record a preference.

## Step 4 — The bundle

Write a **frozen dated bundle** to `harvests/<YYYY-MM-DD>/` in the standards repo (get the date with `date +%Y-%m-%d`; create the folder if absent; never edit a prior harvest):

- `01_COLLECTION_STATE.md` — repos read, roster drift both ways, each repo's last audit/review dates and the standard version each was measured against, and the standard version this run harvests into.
- `02_FINDINGS.md` — every finding, by category, with full citations, the repo count, and its filter outcome (live / settled-by-date / duplicate-of-open-evolution / below-bar).
- `03_EVIDENCE.md` — the verbatim excerpts the findings rest on, quoted with their source. When one quirk was written up several times, quote **all** the versions here and mark which one is deepest.
- `04_PROPOSALS.md` — the proposals that cleared the filters, each with: the target section, the proposed change, the evidence count, the bump classification, and the rollout debt it would create.
- `05_RIPPLE_PLAN.md` — for each proposal, every file the change must touch (Step 6's checklist, resolved to actual paths).
- `06_OUTCOME.md` — written after the interview: what was accepted, deferred, rejected, and why, plus the rollout debt for what landed.

## Step 5 — Interview, one proposal at a time

Present each proposal with its evidence and take a decision: **accept** (apply now), **defer** (record in `open-evolutions.md` with the evidence, so the next run finds a strengthened case rather than starting over), or **reject** (record in `06_OUTCOME.md` with the reason, so the next harvest does not re-propose it).

**Never auto-resolve an ambiguous signal.** For a MUST that N repos fail, and for a standard-internal contradiction, state **both** readings with the counts and ask. You have the evidence; you do not have the authority to decide whether the collection or the rule is wrong, and that decision is not recoverable from the evidence alone.

Keep the standard's own bar in view: it is a document whose changelog entries argue their case from evidence and name the pass they came from. A proposal that cannot be written that way is not ready, however true it might be.

## Step 6 — Apply, with the whole ripple

For each accepted proposal, touch **every** one of these that applies — resolving each through the Sections list and the repo's own links rather than assuming a path:

1. **The section file** — the normative change itself.
2. **`standards/STANDARDS.md`** — the Sections list blurb for that section, if the change alters what the section covers.
3. **The anti-patterns range** — adding an anti-pattern changes the `#1–#N` range cited in the Sections list. The number in the blurb and the last entry in the file must agree.
4. **The changelog entry** at the top of `STANDARDS.md`, in the house register: what changed, why, the evidence, the bump classification, and the pass it was drawn from.
5. **The version bump** — front matter version and date.
6. **`standards/NEW_ADDON_CONTEXT.md`** — if the change affects how a new addon is born, plus the pack's own version.
7. **`standards/EXECUTIVE_SUMMARY.md`** — the summary and its current-version pointer.
8. **The playbooks** — `AUDIT.md` and `NEW_ADDON.md`, if the change alters how a run is structured or what gets checked.
9. **`standards/ADDONS.md`** — only if the roster itself changed.

**The ripple is the dangerous part of this command, not the rule change.** A rule edited in its section and missed in the index, the pack or a playbook leaves the standard **contradicting itself**, and the contradiction is worse than the old rule: an agent reading the stale copy follows it, and nothing goes red. The standard has already spent a whole patch release cleaning up one incomplete ripple — a count left saying "quartet" beside three named members, which an agent completed from memory with the very file the release had deleted. Treat `05_RIPPLE_PLAN.md` as a checklist to be discharged item by item, and record in `06_OUTCOME.md` which touches applied and which were genuinely not applicable.

**Classify the bump explicitly**, in the changelog entry, in these terms:

- **Patch** — no rule changes; wording, fixes, completing a prior ripple. An addon compliant before is compliant after.
- **Minor** — a rule changed such that **an addon can become non-compliant**. Say so in those words, and say what the fix looks like. Call out the two special shapes the standard already recognizes: a MUST an addon satisfies by **deleting** something, and one it satisfies by **doing nothing** (re-vendoring picks it up).
- **Major** — reserved for a restructuring of the standard itself; confirm with the user before claiming one.

## Step 7 — Name the rollout debt, then stop

A rule change that lands with no adoption list is a rule the collection silently fails. Close with, per accepted proposal:

- **Which repos it makes non-compliant**, named — you have just read all of them, so this is knowledge no later run recovers as cheaply.
- **What each repo needs**: `/wow-addon:standards-audit` to measure it, `/wow-addon:revendor-standards` to carry the new text and any new vendored quirks down.
- Whether the change requires a **`LibKa0s` change first** — if so, that repo leads and must be pushed before consumers cite it (`/wow-addon:finalize` enforces that ordering).

Then print the harvest summary: repos read, findings by category, proposals accepted / deferred / rejected, the new standard version, the bundle path.

**Do not commit and do not push.** Review the diff first; `/wow-addon:finalize` owns landing it.

## Hard rules

- **Read-only on every addon repo and on `LibKa0s`.** Your only writes are inside the `WowAddonStandards` repo. Never edit a frozen `docs/audits/` or `docs/reviews/` bundle anywhere.
- **Never propose a rule without citations.** Two repos, or one plus a stated cost. Below the bar goes to the watch list, not the standard.
- **Never auto-resolve an ambiguous signal.** Both readings, with counts, and ask.
- **Never hard-code a section filename.** Discover every one from the `STANDARDS.md` Sections list — including the quirks catalogue.
- **Never edit a prior `harvests/<date>/`.** Frozen, like every other dated bundle.
- **Never skip the ripple.** A partial ripple is worse than no change.
- **Don't lower the standard's register.** Its rules carry their reasons, because a rule without its reason is deleted by the next author who finds it inconvenient. Write proposals the same way.
- **Don't harvest from a single repo and call it a collection finding.** Cross-repo synthesis is the whole point; a one-repo finding is a watch-list item until a second repo agrees.
- **Don't commit, don't push, don't bump an addon's version.** Nothing in this run touches an addon.

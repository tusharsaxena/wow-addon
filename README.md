# wow-addon

Claude Code plugin for World of Warcraft addon development.

A focused toolkit for working on WoW addons: scaffolding new addons that are born compliant with the Ka0s WoW Addon Standard, auditing an addon against that standard, bumping an addon's interface version to match Live Servers, syncing documentation against the actual code, releasing new versions, running the addon's test battery, triaging everything still pending across its code, docs, issues and prior audit plans, managing its GitHub issues, and reviewing changes for WoW-specific correctness (taint, deprecated APIs, frame leaks, missing localization, AceConfig misuse, dead code).

`/wow-addon:new-addon` and `/wow-addon:standards-audit` consume the living **Ka0s WoW Addon Standard** at [tusharsaxena/WowAddonStandards](https://github.com/tusharsaxena/WowAddonStandards): they fetch that repo's `NEW_ADDON.md` / `AUDIT.md` playbooks and `standards/` docs at runtime and follow them, so they always track the current standard. Both need network access to that public repo when they run.

## Components

### Commands

| Command | What it does |
|---|---|
| `/wow-addon:new-addon <Name>` | Scaffold a new addon born compliant with the Ka0s WoW Addon Standard. Fetches the `NEW_ADDON.md` playbook + context pack and follows them: Ace3 skeleton, the modular layout, MIT, the canonical `docs/` trio (`ARCHITECTURE.md`, `testing.md`, `smoke-tests.md`) and a `CLAUDE.md` stub — the context pack itself is read at runtime and **never** written into the addon (`documentation-§3`). The shared subsystems — chat printer, debug console, options toolkit, slash dispatcher, perf harness, test harness — are **consumed** from the vendored `LibKa0s` library and its test kit, one setup file per adopted module, rather than hand-built. |
| `/wow-addon:bump-interface [number]` | Update `## Interface:` in the current addon's TOC(s) to the current Retail (Live Servers) value. This repo only, not recursive. Pass the number, or omit it to use the current Live value (asks to confirm if unsure). |
| `/wow-addon:sync-docs` | Deep-analyze the addon and rewrite `README.md` / `CLAUDE*.md` / `ARCHITECTURE*.md` to eliminate drift. Includes count verification, COMMANDS↔README slash parity, dead-export detection, and ARCHITECTURE.md scaffolding. |
| `/wow-addon:bump-version [X.Y.Z]` | Bump the addon's version everywhere it appears (TOC, code, README badges, "What's new" section, Version History table, `CLAUDE*.md`) and write the CHANGELOG entry for everything since the last git tag. Proposes a bump if no version is given. |
| `/wow-addon:diff` | Summarize all uncommitted git changes in the addon — what changed, likely intent, risks. |
| `/wow-addon:commit` | Stage and commit changes with a generated commit message that matches the project's style. |
| `/wow-addon:finalize [repos]` | Finish a changeset — in the current repo alone, or across several sibling repos. Establishes the scope first and **never guesses**: explicit repos (or `here`) if you pass them, the single dirty repo if there is only one, all of them when hard evidence proves one changeset — otherwise it prints each candidate's changes and asks. With more than one repo in scope it derives the dependency chain from evidence — a vendored shared library is finalized and **pushed** before the consumers that carry it, and a doc line citing `../<Repo>/…` is an edge like any other — then, per repo: `sync-docs` (content only in a parallel multi-repo run, since nobody is there to confirm per repo; it asks as usual in a single-repo run), that repo's own gate including the vendor-drift diff, `commit`, merge any feature branch with `--no-ff`, push, and delete the branch with `-d`. Independent repos run in parallel, one agent per repo. A red gate, a merge conflict or a rejected push stops that repo alone and is reported with its real output. The one command that deliberately pushes. |
| `/wow-addon:run-tests` | Run the addon's entire test battery — auto-detects and runs luacheck lint, the headless Lua `tests/` harness, and any Makefile `test` target, then reports a combined pass/fail summary. Offers to diagnose and fix failures. Deliberately skips non-gating measurement runners such as `tests/perf.lua`: they measure rather than verify, and their scenarios are not test cases. Treats the vendored `tests/_kit/` harness as harness, not a suite, and surfaces a kit-sync (vendor-drift) failure distinctly, since its fix is a re-vendor rather than an edit. |
| `/wow-addon:pending-audit [scope]` | Sweep the addon for everything still hanging — TODO/FIXME/stub markers, unexecuted items from the newest audit and review execution plans, doc open questions and Known Limitations, an `Unreleased` CHANGELOG section, open GitHub issues, stashes and follow-up commits, and recorded-but-unacted Claude memory. Bucketizes by type (decision / action / deferred) and severity, then asks whether you want to triage now or just take the inventory and stop. If you triage, it interviews you one item at a time with tailored options — every item can also be deferred, either into the ledger alone or into the ledger plus a filed GitHub issue for work that needs to be visible outside your working copy, or closed as "will not do" (never) — implements what you accept, and records the decisions in `docs/pending/LEDGER.md` so deferred items stay quiet and closed ones never come back. Pass `code`, `docs`, `issues`, `memory`, or a path to narrow the sweep. |
| `/wow-addon:fetch-issues [filter]` | List the GitHub issues open on the addon's repo (via `gh`). Optionally filter by label, or pass `closed`/`all`. Read-only. |
| `/wow-addon:add-issue` | Create a well-formed GitHub issue (via `gh`). Gathers a title, tag (bug/enhancement), and details — fuzzy input is fine — formulates a clean issue, shows it for approval, then creates it. |

### Subagents

| Agent | When to invoke |
|---|---|
| `review` | Focused review of WoW-specific issues: taint and combat lockdown (incl. secret-value leakage), event over-registration, frame leaks, deprecated APIs, missing localization, AceConfig/Settings UI misuse, NBSP/tooltip-pattern bugs, dead exports, and project-internal convention drift (COMMANDS dispatcher parity, single-write-path bypass — applied only when the addon has those conventions). Vets its own findings and proposed changes against the living Ka0s WoW Addon Standard so remediation never introduces a new deviation — a guardrail, not a full audit (that's `standards-audit`); if the standard can't be fetched it proceeds anyway and notes the skip. Treats vendored code (`libs/`, `tests/_kit/`) as read-only: a defect there is reported as an `[upstream]` finding to fix in the library repo and re-vendor, never a local patch. For subsystems the addon consumes from a shared library, it reviews the **descriptor** and the **degradation stub** — not the library's implementation — and never proposes re-hand-rolling what the library provides. Invoked via `/wow-addon:review`. |
| `standards-audit` | Read-only compliance audit against the Ka0s WoW Addon Standard. Fetches the living `AUDIT.md` playbook + `standards/STANDARDS.md` (the standard's index) at runtime, follows the index's Sections list to fetch every section file, measures the addon section-by-section and against the `anti-patterns` list, and writes a frozen `docs/audits/<YYYY-MM-DD>/` bundle (current state, deviations with stable IDs, evidence, remediation design, execution plan). Runs the mechanical checks rather than reasoning about them — lint, the headless suite, and a `diff -r` of every vendored Ka0s-owned library against its sibling source repo, since that drift is invisible to both repos' test suites. Never modifies addon code. Invoked via `/wow-addon:standards-audit`. |

### Hooks

- **CRLF normalization on Write/Edit/MultiEdit** — when a file is written/edited inside a git repo whose `.gitattributes` declares `eol=crlf` for that file, the plugin auto-normalizes line endings to CRLF. Silent on non-applicable files. Lives at `hooks/hooks.json` + `scripts/normalize-crlf.sh`.

## Install

Install straight from this GitHub repo — no manual cloning required. In any Claude Code session, run these three commands:

```
/plugin marketplace add tusharsaxena/wow-addon
/plugin install wow-addon@wow-addon
/reload-plugins
```

Step by step:

1. **`/plugin marketplace add tusharsaxena/wow-addon`** — registers this repo as a plugin marketplace. Claude Code clones it for you. (You can also pass the full URL `https://github.com/tusharsaxena/wow-addon.git` or, if you already have a local clone, the path to it.)
2. **`/plugin install wow-addon@wow-addon`** — installs the plugin (`wow-addon`) from the marketplace (`wow-addon`). When prompted for scope, choose **user** to enable it in every project on this machine, or **project** to enable it only in the current project.
3. **`/reload-plugins`** — activates the plugin in the current session without a restart.

After install, the commands, the `review` and `standards-audit` subagents, and the CRLF hook are available in every Claude Code session.

## Updating

When the repo changes (new commands, updated agent, new hook), pull the latest and reload:

```
/plugin marketplace update wow-addon
/reload-plugins
```

## License

MIT.

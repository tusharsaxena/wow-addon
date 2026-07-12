# wow-addon

Claude Code plugin for World of Warcraft addon development.

A focused toolkit for working on WoW addons: scaffolding new addons that are born compliant with the Ka0s WoW Addon Standard, auditing an addon against that standard, bumping an addon's interface version to match Live Servers, syncing documentation against the actual code, releasing new versions, running the addon's test battery, managing its GitHub issues, and reviewing changes for WoW-specific correctness (taint, deprecated APIs, frame leaks, missing localization, AceConfig misuse, dead code).

`/wow-addon:new-addon` and `/wow-addon:standards-audit` consume the living **Ka0s WoW Addon Standard** at [tusharsaxena/WowAddonStandards](https://github.com/tusharsaxena/WowAddonStandards): they fetch that repo's `NEW_ADDON.md` / `AUDIT.md` playbooks and `standards/` docs at runtime and follow them, so they always track the current standard. Both need network access to that public repo when they run.

## Components

### Commands

| Command | What it does |
|---|---|
| `/wow-addon:new-addon <Name>` | Scaffold a new addon born compliant with the Ka0s WoW Addon Standard. Fetches the `NEW_ADDON.md` playbook + context pack and follows them: Ace3 skeleton, tier layout, MIT, the standards brief dropped into the addon's `docs/`, and a `CLAUDE.md` stub. |
| `/wow-addon:bump-interface [number]` | Update `## Interface:` in the current addon's TOC(s) to the current Retail (Live Servers) value. This repo only, not recursive. Pass the number, or omit it to use the current Live value (asks to confirm if unsure). |
| `/wow-addon:sync-docs` | Deep-analyze the addon and rewrite `README.md` / `CLAUDE*.md` / `ARCHITECTURE*.md` to eliminate drift. Includes count verification, COMMANDS↔README slash parity, dead-export detection, and ARCHITECTURE.md scaffolding. |
| `/wow-addon:bump-version [X.Y.Z]` | Bump the addon's version everywhere it appears (TOC, code, README badges, Version History table, CHANGELOG). Proposes a bump if no version is given. |
| `/wow-addon:diff` | Summarize all uncommitted git changes in the addon — what changed, likely intent, risks. |
| `/wow-addon:commit` | Stage and commit changes with a generated commit message that matches the project's style. |
| `/wow-addon:run-tests` | Run the addon's entire test battery — auto-detects and runs luacheck lint, the headless Lua `tests/` harness, and any Makefile `test` target, then reports a combined pass/fail summary. Offers to diagnose and fix failures. |
| `/wow-addon:fetch-issues [filter]` | List the GitHub issues open on the addon's repo (via `gh`). Optionally filter by label, or pass `closed`/`all`. Read-only. |
| `/wow-addon:add-issue` | Create a well-formed GitHub issue (via `gh`). Gathers a title, tag (bug/enhancement), and details — fuzzy input is fine — formulates a clean issue, shows it for approval, then creates it. |

### Subagents

| Agent | When to invoke |
|---|---|
| `review` | Focused review of WoW-specific issues: taint and combat lockdown (incl. secret-value leakage), event over-registration, frame leaks, deprecated APIs, missing localization, AceConfig/Settings UI misuse, NBSP/tooltip-pattern bugs, dead exports, and project-internal convention drift (COMMANDS dispatcher parity, single-write-path bypass — applied only when the addon has those conventions). Invoked via `/wow-addon:review`. |
| `standards-audit` | Read-only compliance audit against the Ka0s WoW Addon Standard. Fetches the living `AUDIT.md` playbook + `standards/01_STANDARD.md` at runtime, measures the addon section-by-section and against the §19 anti-patterns, and writes a frozen `audit/<YYYY-MM-DD>/` bundle (current state, deviations with stable IDs, evidence, remediation design, execution plan). Never modifies addon code. Invoked via `/wow-addon:standards-audit`. |

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

# wow-addon

Claude Code plugin for World of Warcraft addon development.

A focused toolkit for working on WoW addons: scaffolding new addons, bumping interface versions across a project, syncing documentation against the actual code, normalizing READMEs across multiple addons, auditing cross-addon convention drift, releasing new versions, and reviewing changes for WoW-specific correctness (taint, deprecated APIs, frame leaks, missing localization, AceConfig misuse, dead code).

## Components

### Commands

| Command | What it does |
|---|---|
| `/wow-addon:new-addon <Name>` | Scaffold a new addon (Ace3 stack, MIT, modular layout). Adapts to sibling addons' conventions when present. |
| `/wow-addon:bump-interface <versions>` | Update `## Interface:` in every `.toc` under the cwd (recursive). |
| `/wow-addon:sync-docs` | Deep-analyze the addon and rewrite `README.md` / `CLAUDE*.md` / `ARCHITECTURE*.md` to eliminate drift. Includes count verification, COMMANDS↔README slash parity, dead-export detection, and ARCHITECTURE.md scaffolding. |
| `/wow-addon:normalize-readme <ref-addon>` | Reshape the cwd addon's README to match the section structure, table conventions, and ordering of a reference addon's README. Inter-addon — does NOT touch code. |
| `/wow-addon:audit-conventions [root]` | Walk every addon under cwd (or given root) and report cross-addon drift in TOC, library versions, structural patterns, docs, and git hygiene. Read-only. |
| `/wow-addon:version-bump [X.Y.Z]` | Bump the addon's version everywhere it appears (TOC, code, README badges, Version History table, CHANGELOG). Proposes a bump if no version is given. |
| `/wow-addon:diff` | Summarize all uncommitted git changes in the addon — what changed, likely intent, risks. |
| `/wow-addon:commit` | Stage and commit changes with a generated commit message that matches the project's style. |

### Subagents

| Agent | When to invoke |
|---|---|
| `review` | Focused review of WoW-specific issues: taint and combat lockdown (incl. secret-value leakage), event over-registration, frame leaks, deprecated APIs, missing localization, AceConfig/Settings UI misuse, NBSP/tooltip-pattern bugs, dead exports, and project-internal convention drift (COMMANDS dispatcher parity, single-write-path bypass — applied only when the addon has those conventions). |

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

After install, the commands, the `review` subagent, and the CRLF hook are available in every Claude Code session.

## Updating

When the repo changes (new commands, updated agent, new hook), pull the latest and reload:

```
/plugin marketplace update wow-addon
/reload-plugins
```

## License

MIT.

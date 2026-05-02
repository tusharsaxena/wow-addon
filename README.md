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

This plugin is distributed as a local marketplace directory. To install:

1. Clone or copy the marketplace directory to your machine. The marketplace is the directory that contains `.claude-plugin/marketplace.json` (one level above `plugins/wow-addon/`).
2. In any Claude Code session, run:

   ```
   /plugin marketplace add <path-to-marketplace-directory>
   /plugin install wow-addon@tushar-local
   /reload-plugins
   ```

3. When prompted for install scope, choose **user** to enable the plugin in every project on this machine. Choose **project** to enable it only in the current project.

After install, the commands, the `review` subagent, and the CRLF hook are available in every Claude Code session.

## Updating

When the marketplace contents change (new commands, updated agent, new hook):

```
/plugin marketplace update tushar-local
/reload-plugins
```

## License

MIT.

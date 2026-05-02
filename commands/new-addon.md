---
description: Scaffold a new WoW addon with the Ace3 stack, modular folder layout, MIT license, AceDB saved variables, and an AceConsole slash command.
argument-hint: <AddonName> [one-line description]
allowed-tools: [Read, Glob, Bash, Write]
---

Scaffold a new WoW addon named **$ARGUMENTS** in the current working directory.

## Defaults to use

Unless the cwd has a `CLAUDE.md` or sibling addons that specify otherwise:

- **Title**: the addon name as given
- **Author**: ask the user once (or read from a sibling addon's `## Author:` line and reuse without asking)
- **Version**: `0.1.0`
- **License**: MIT
- **Saved variable name**: `<AddonName>DB`
- **Library stack**: Ace3 (AceAddon-3.0, AceEvent-3.0, AceConsole-3.0, AceDB-3.0, AceConfig-3.0, AceLocale-3.0)

If sibling addons exist in the parent of cwd, prefer their conventions over the defaults above (author, license, library set, folder layout, packager pragma style).

## Steps

1. **Folder**: create `<AddonName>/` at the cwd. Bail with an error if it already exists.
2. **TOC** at `<AddonName>/<AddonName>.toc`:
   - `## Interface:` — copy the value from the most-recently-modified `.toc` file in the parent of cwd (sibling addons). If none found, ask the user for the target build numbers.
   - `## Title: <AddonName>` (or use the description from `$ARGUMENTS` as `## Notes:`)
   - `## Author: <author>`
   - `## Version: 0.1.0`
   - `## SavedVariables: <AddonName>DB`
   - `## DefaultState: enabled`
   - `## Category-enUS: <ask user, or default to "Miscellaneous">`
   - `## X-License: MIT`
   - Then the load order: locales, core, modules, settings (omit sections you're not creating).
3. **Folder structure** — create empty placeholder dirs and files:
   - `core/<AddonName>.lua` — main file with the Ace3 skeleton: `local addonName, ns = ...`; `local addon = LibStub("AceAddon-3.0"):NewAddon(addonName, "AceEvent-3.0", "AceConsole-3.0", "AceDB-3.0")`; `function addon:OnInitialize()` builds the db and registers `/<addonname>`; `function addon:OnEnable()` registers `PLAYER_ENTERING_WORLD`.
   - `core/Schema.lua` — `local _, ns = ...; ns.defaults = { profile = { enabled = true }, char = {}, global = {} }`.
   - `locales/enUS.lua` — `local L = LibStub("AceLocale-3.0"):NewLocale("<AddonName>", "enUS", true); if not L then return end`.
   - `libs/.gitkeep` — empty (libs are pulled by the packager via `.pkgmeta`).
   - `media/.gitkeep` — empty.
4. **README.md**: a short stub — title, the description as the lede, and an "Install" section with placeholder URLs the user will fill in (CurseForge, Wago, WoWInterface).
5. **LICENSE**: MIT, current year, copyright holder = `<author>`.
6. **`.pkgmeta`**:
   ```yaml
   package-as: <AddonName>
   externals:
     libs/LibStub:
       url: https://repos.wowace.com/wow/libstub/trunk
     libs/CallbackHandler-1.0:
       url: https://repos.wowace.com/wow/callbackhandler/trunk/CallbackHandler-1.0
     libs/AceAddon-3.0:
       url: https://repos.wowace.com/wow/ace3/trunk/AceAddon-3.0
     libs/AceEvent-3.0:
       url: https://repos.wowace.com/wow/ace3/trunk/AceEvent-3.0
     libs/AceConsole-3.0:
       url: https://repos.wowace.com/wow/ace3/trunk/AceConsole-3.0
     libs/AceDB-3.0:
       url: https://repos.wowace.com/wow/ace3/trunk/AceDB-3.0
     libs/AceLocale-3.0:
       url: https://repos.wowace.com/wow/ace3/trunk/AceLocale-3.0
   ignore:
     - .git
     - .github
     - .gitignore
     - CLAUDE.md
   enable-nolib-creation: yes
   ```
7. **CLAUDE.md**: a short file declaring the project conventions for future Claude sessions in this addon (Ace3 stack, `<AddonName>DB` saved-vars name, MIT, modular `core/modules/settings/locales` layout). Keep it under 30 lines.

After scaffolding, print:
- The created file tree (just the paths).
- The exact `## Interface:` value used and where it was copied from.
- A reminder to run the packager (or fetch libs manually) before first use, since `libs/` is empty.

Do not create `git init`, hooks, or CI files unless the user asks.

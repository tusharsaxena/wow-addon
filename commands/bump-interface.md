---
description: Bump the ## Interface line in the current addon's TOC(s) to the current Retail (Live Servers) interface number. Operates on this repo only (not recursive). Pass the number explicitly, or the command determines the current Live value and asks you to confirm if unsure.
argument-hint: [interface-number] (optional, e.g. 120000 — omit to use the current Live Servers value)
allowed-tools: [Read, Glob, Grep, Edit, Bash]
---

Bump the `## Interface:` line in the **current addon repo's** TOC file(s) to the current **Retail / Live Servers** interface number. Scope is this one addon — do **not** walk into subdirectories hunting for other addons.

## Resolve the target interface number

1. If `$ARGUMENTS` is non-empty, use it as the target. Validate it looks like a 6-digit build number (e.g. `120000`); if it's a comma-separated list, accept it verbatim (some TOCs carry multiple). If the format looks wrong, stop and ask the user to confirm.
2. If `$ARGUMENTS` is empty, determine the **current Live Servers (Retail) interface number** — the value currently live on the retail realms, which is `(major * 10000) + (minor * 100) + patch` for the current retail patch (e.g. patch 11.1.5 → `110105`).
   - **If you are not certain** what the current Live interface number is (it changes every patch and your knowledge may be stale), **do not guess** — ask the user: *"What's the current Live Servers interface number? (e.g. 110105 for patch 11.1.5)"* and use their answer. Getting this wrong makes the addon show as out-of-date in-game, so confirming beats guessing.

## Find the TOC(s)

Look for `*.toc` files at the **top level of the current repo only** (the addon root). Include the main TOC and any per-flavor Retail TOCs beside it (`Foo.toc`, `Foo_Mainline.toc`). Do **not** recurse into subfolders, and skip `libs/`, `Libs/`, `.git/`.

- If there are zero top-level `.toc` files, stop and tell the user this doesn't look like an addon repo root (suggest they `cd` into the addon).
- If a TOC targets a non-Retail flavor (e.g. `_Vanilla`, `_Cata`, `_Wrath`), leave it alone and report it as skipped — the Live Servers value is Retail-only.

## Apply

For each Retail TOC:
- Read the file.
- Replace the line starting with `## Interface:` (case-insensitive on the key) with `## Interface: <target>`.
- If no `## Interface:` line exists, leave the file alone and report it as skipped.

Use `Edit` for a surgical single-line change; preserve the file's existing line endings.

## Report

Print a summary table: `TOC | Old value | New value | Status (updated / unchanged / skipped)`. State which interface number was used and how it was resolved (passed as argument / determined as current Live / confirmed by user).

Do **not** commit or stage anything — the user reviews the diff themselves.

---
description: Bump the ## Interface line in every .toc file in the working directory (recursive). Pass the new comma-separated build numbers.
argument-hint: <interface-numbers> (e.g. 120000,120001,120005)
---

Bump the `## Interface:` line in every `.toc` file under the current working directory to: **$ARGUMENTS**

Steps:

1. Validate `$ARGUMENTS` looks like a comma-separated list of 6-digit build numbers (e.g. `120000,120001,120005`). If it doesn't, stop and ask the user to confirm the format.
2. Find every `*.toc` file under the cwd (recursive). Skip anything inside `libs/`, `Libs/`, `.git/`, or `node_modules/`.
3. For each TOC:
   - Read the file.
   - Replace the line that starts with `## Interface:` (case-insensitive on the key) with `## Interface: $ARGUMENTS`.
   - If no `## Interface:` line exists, leave the file alone and report it as skipped.
4. Print a summary table:
   - Path | Old value | New value | Status (updated / unchanged / skipped)
5. Do NOT commit or stage anything. The user reviews the diffs themselves.

If the cwd contains zero `.toc` files, suggest the user `cd` into their addons root and re-run.

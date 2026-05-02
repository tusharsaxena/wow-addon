---
description: Bump the addon version to X.Y.Z everywhere it appears — TOC, code constants, README badges and Version History table, CLAUDE*.md, CHANGELOG. Asks for the version if not provided.
argument-hint: [X.Y.Z]
allowed-tools: [Read, Glob, Grep, Bash, Edit]
---

Bump the version of the addon in the current working directory.

## Step 1 — Determine the new version

If `$ARGUMENTS` is non-empty and looks like a semver (`X.Y.Z` or `X.Y.Z-tag`), use it as the new version.

Otherwise:
1. Find the current version. Check, in this order: the `.toc` file's `## Version:` line, then any `local VERSION = "..."` / `MAJOR_VERSION` constant in the code, then the README's "Version" mention.
2. Propose a bump:
   - **patch** (`X.Y.Z` → `X.Y.Z+1`): the safe default for bugfixes / small changes
   - **minor** (`X.Y.Z` → `X.Y+1.0`): for new features
   - **major** (`X.Y.Z` → `X+1.0.0`): for breaking changes
   Recommend one with a one-line reason based on what's in the working tree (`git status` / `git diff` if it's a git repo, otherwise a quick scan of recent file mtimes).
3. Ask the user: "Current version is X.Y.Z. Propose bumping to A.B.C ([reason]). Confirm or specify another version."
4. Wait for the user's reply before proceeding.

## Step 2 — Find every version reference

Search the addon root recursively (skip `libs/`, `Libs/`, `.git/`, `node_modules/`) for the **current** version string. Targets to check explicitly (don't rely on the regex search alone for these — verify each):

**Code & TOC**
- `## Version:` line(s) in every `.toc` (including per-flavor variants: `*_Mainline.toc`, `*_Cata.toc`, etc.)
- `VERSION =`, `ADDON_VERSION =`, `MAJOR_VERSION =`, `MINOR_VERSION =`, `version = ` in `.lua`
- Any string literal matching the current semver in `.lua` and `.xml`

**README**
- The "Version" heading or text mention near the top
- **Shields.io badge URLs** that include the version. Common shapes:
  - `https://img.shields.io/badge/version-X.Y.Z-...`
  - `https://img.shields.io/curseforge/v/<id>` (auto-derived — leave alone)
  - `https://img.shields.io/github/v/release/<owner>/<repo>` (auto-derived — leave alone)
  - Manually-pinned badges with the version in the path or `?label=` parameter
- **"Version History" table** at the bottom of the README — this lists OLD versions as facts, not "the current version". Add a NEW row for the new version with an auto-generated summary of changes since the last version bump (see Step 3). Do NOT rewrite existing rows.

**Other docs**
- `CLAUDE*.md` mentions of the version
- `ARCHITECTURE*.md` mentions
- `CHANGELOG.md` — if there's an "Unreleased" header, change it to the new version + today's date. If there's no CHANGELOG, don't create one. Do NOT rewrite past entries.
- `.pkgmeta` if it pins a version explicitly

**Auto-substituted (do NOT touch)**
- `## Version: @project-version@` (BigWigsMods packager substitution) — leave alone, version comes from git tag at build time
- Auto-derived shields badges (CurseForge, GitHub release) — leave alone
- Note any of these to the user as "skipped because auto-derived"

Report the full list of matches **before** editing.

## Step 3 — Summarize changes since the last version

Generate a concise, user-visible summary of changes since the previous version. This summary populates the new README "Version History" row in Step 4.

**Determine the "since" reference**, in this order:
1. Git tag matching the previous version. Try `git tag --list 'v<previous>' '<previous>'`.
2. The commit that last set the version constant to the previous value. Find via `git log -G '"<previous>"' -- <files-from-Step-2>` and pick the most recent commit that *introduced* the previous version (typically the previous version-bump commit).
3. The date in the row above the new one in the README's Version History table — use `git log --since=<date>` as a fallback window.
4. If none of the above can be determined, leave the row's summary empty and warn the user that no `since` reference was found.

**Collect change material**, prefer in this order:
1. If `CHANGELOG.md` has a populated `## [Unreleased]` (or equivalent) section, use those bullets as the source — they are the user's authoritative list. Condense for the README row; do not re-derive from git on top.
2. Otherwise, derive from git: `git log <since>..HEAD --oneline` for commit subjects, `git diff --stat <since>..HEAD` for scope, and full commit bodies (`git log <since>..HEAD`) for context on non-trivial commits.

**Write the summary**:
- Group bullets by category in this order: **Added**, **Changed**, **Fixed**, **Removed**, **Deprecated**, **Docs**, **Internals**. Skip categories with nothing.
- Past tense, user-visible language ("Added /foo command", "Fixed taint regression on PLAYER_REGEN_DISABLED") — not commit-message phrasing.
- Keep it tight: ~3–8 bullets total. Roll up trivia (whitespace, lint, formatting, dependency bumps) into a single "Internals" bullet rather than listing each.
- Format for a markdown table cell: separate bullets with `<br>` so the cell stays one row. Example: `Added /foo command<br>Fixed taint on combat exit<br>Updated deDE locale`.
- No commit hashes, PR numbers, or author names in the README row.

## Step 4 — Update

For each match, replace the old version with the new version using `Edit`. Be precise — match the exact context to avoid touching unrelated strings (e.g. don't replace `1.0.0` if it's an Interface number, a library version, or a Lua version requirement).

For the README "Version History" table: insert a NEW row at the top (or wherever the table is ordered to put the latest), with the new version and the summary from Step 3 in the release-notes cell. Do NOT modify existing rows.

For `CHANGELOG.md`: if an "Unreleased" or `## [Unreleased]` header exists, rewrite it to `## [X.Y.Z] — YYYY-MM-DD` with today's date. Do NOT generate the CHANGELOG change list — that's the user's job. (Different from the README row, which IS auto-filled.)

## Step 5 — Report

Print:
- Old version → New version
- Every file changed (path + the line that was updated)
- Every version-shaped string found but DID NOT change (with reason — e.g. "looks like a library version, not the addon's version", "auto-derived CurseForge badge", "BigWigsMods @project-version@ substitution")
- Reminder: tag the commit with `vX.Y.Z` if using the BigWigsMods packager (the packager picks the version up from the latest git tag)

## Hard rules

- **Don't commit.** The user reviews the diffs first.
- **Don't tag.** Tagging is a deliberate user action.
- **Don't write a CHANGELOG.md entry's body from scratch** — only rewrite an existing "Unreleased" header. If no CHANGELOG, don't create one. (The README Version History row's summary IS auto-generated — Step 3 — that's a different file with a different rule.)
- **Don't modify existing Version History rows** — only add a new row for the new version.
- **Don't bump the Interface version.** That's `/wow-addon:bump-interface`.

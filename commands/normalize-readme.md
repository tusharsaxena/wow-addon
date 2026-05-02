---
description: Reshape the cwd addon's README to match the section structure, table conventions, and ordering of a reference addon's README. Inter-addon — does NOT touch code.
argument-hint: <path-to-reference-addon>
allowed-tools: [Read, Glob, Grep, Bash, Edit, Write]
---

Reshape the README of the addon in the current working directory so its section structure matches the README of a reference addon at: **$ARGUMENTS**

This is **inter-addon README normalization** — distinct from `/wow-addon:sync-docs` (which reconciles docs against code in the *same* addon). Here you're propagating one addon's README *shape* (sections, ordering, table conventions, FAQ/Troubleshooting style, badge layout) to another addon, while keeping the content addon-specific.

## Step 1 — Validate inputs

1. Resolve `$ARGUMENTS` to an absolute path. If it doesn't exist, or doesn't contain a `README.md` at its root, stop and ask for a corrected path.
2. The cwd must contain a `README.md`. If not, stop and ask the user to either `cd` to the right addon or run `/wow-addon:new-addon` first.
3. The cwd must contain at least one `.toc` (it's a WoW addon). If not, stop with a clear error.
4. The reference and the cwd must be different paths. If they're the same, stop.

## Step 2 — Parse both READMEs

For both the reference and the cwd README, build a structural outline:
- Title line (H1)
- Badge row (the `[![...](shields.io/...)](...)` block immediately under the title, if present)
- Logo / hero image (if present)
- Section list: every `##` heading in order, with sub-headings (`###`) nested under each
- For each section, classify the content type:
  - **prose** — paragraphs of text
  - **bullet-list** — `- item` lines
  - **table** — pipe-delimited table
  - **code-block** — fenced code
  - **mixed** — combination
- Note any embedded screenshots (image links inside sections)
- Note presence/absence of "Version History" table at the end

## Step 3 — Diff the structures

Build a normalized diff:

**Section-level**
- Sections present in reference but missing from cwd → `MISSING`
- Sections present in cwd but absent from reference → `EXTRA` (don't auto-delete; flag for the user — these are usually intentional addon-specific content)
- Sections present in both but in different order → `REORDER`
- Sections present in both with mismatched content type (e.g. reference uses a table for Slash Commands, cwd uses a bullet list) → `CONVERT`

**Sub-section-level (inside common sections)**
- Same checks one level deeper

**Top-of-file elements**
- Title casing/style differs → `RETITLE`
- Badge row missing or has different badges → `BADGES` (note which badges to add — CurseForge version, WoW Interface badge, license)
- Logo image missing → `LOGO`

**Bottom-of-file elements**
- Version History table missing → `VERSION-HISTORY`

## Step 4 — Plan, then ask

Print the diff as a structured plan:

```
NORMALIZE README — reference: <ref-name>, target: <cwd addon name>

MISSING sections (will add empty stubs you fill in):
  - ## FAQ
  - ## Troubleshooting

EXTRA sections (will keep — flag for review):
  - ## Donations  (not in reference; intentional?)

REORDER:
  - ## Usage was after ## Configuration; reference puts Usage first
  - ## Version History is currently above ## License; reference puts it last

CONVERT:
  - ### Slash commands: bullet list → table (matching reference's columns: Command | What it does)

BADGES: missing CurseForge version badge; reference uses:
  [![CurseForge](https://img.shields.io/curseforge/v/<id>?label=CurseForge)](https://www.curseforge.com/wow/addons/<slug>)

LOGO: reference has a hero image at the top; cwd has none. Will leave a placeholder.

RETITLE: reference uses "Ka0s <Name>" style title; cwd currently uses "<Name>". Will leave cwd as-is unless told otherwise.
```

Then ask: **"Apply this plan? (y / n / specific items to skip)"**

Wait for the user's reply. If they say "skip X", drop those items from the plan and re-show.

## Step 5 — Apply

For each accepted change:
- **MISSING sections**: insert in the correct position. Body = a one-line stub like `_TODO: describe <section>._` so the user knows to fill it in.
- **EXTRA sections**: leave untouched. Print "kept: <section>" in the report.
- **REORDER**: move sections by cut/paste; preserve their full content verbatim.
- **CONVERT**: reformat the content (e.g. bullet list → table) preserving every fact.
- **BADGES / LOGO / RETITLE / VERSION-HISTORY**: insert with placeholder URLs/IDs the user fills in (e.g. `<curseforge-id>`, `<addon-slug>`).

Use `Edit` for surgical changes. Use `Write` (full rewrite) only if the diff would be larger than the rewrite.

**Preserve line endings.** Detect the cwd README's line endings (LF or CRLF) and write the same. If `.gitattributes` declares CRLF for `.md` files, the plugin's CRLF hook will handle this — but get it right on the first write so the diff stays clean.

## Step 6 — Report

Print:
- Sections added / reordered / converted (with line numbers)
- Items left for the user (placeholders to fill in: badges, screenshots, FAQ content, etc.)
- Anything you couldn't reconcile (ambiguous mapping between reference and cwd content)
- A reminder to review the diff and fill in placeholders before committing

## Hard rules

- **Don't touch code, TOC, LICENSE, CHANGELOG, CLAUDE*.md, or ARCHITECTURE*.md.** README only.
- **Don't fabricate addon-specific content.** If a section in the reference has rich addon-specific text, the cwd version gets a stub, not the reference's text.
- **Don't delete EXTRA sections without explicit user approval.**
- **Don't commit.**

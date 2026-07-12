---
description: Scaffold a new Ka0s WoW addon that is born compliant with the Ka0s WoW Addon Standard. Fetches the NEW_ADDON.md playbook + the standards context pack from the WowAddonStandards repo at runtime and follows them to the letter — Ace3 skeleton, tier layout, MIT, the standards brief dropped into the addon's docs/, and a CLAUDE.md stub so future agents build the rest against the standard.
argument-hint: <AddonName> [one-line description]
allowed-tools: [Read, Glob, Grep, Bash, Write, WebFetch]
---

Scaffold a new WoW addon named **$ARGUMENTS** in the current working directory, **born compliant** with the Ka0s WoW Addon Standard. You do not carry the scaffolding rules yourself — the canonical rules and the new-addon procedure live in the `WowAddonStandards` repo and evolve there. Fetch the current playbook and context pack, then **follow them to the letter**.

## Standards source

The living standard lives at `https://github.com/tusharsaxena/WowAddonStandards`. Read its files from the raw base:

```
RAW=https://raw.githubusercontent.com/tusharsaxena/WowAddonStandards/master
```

## Step 0 — Resolve the playbook and the context pack (do this first)

Fetch these **faithfully** (see the fetch rule below), in order:

1. `$RAW/NEW_ADDON.md` — the new-addon playbook. It is authoritative for *how the addon is scaffolded*: the 8 steps, the tier choice, the identity defaults, and the hard rules.
2. `$RAW/standards/02_NEW_ADDON_CONTEXT.md` — the full context pack: kickstart walkthrough, tier trees, starter snippets (TOC, entry, `Compat`, `Locale`, `Database`, `Settings`, debug console, tests, message bus, `.luacheckrc`, `.pkgmeta`), hard-rules cheat sheet, and the Definition-of-Done checklist. **Its contents get dropped into the new addon** (see below).
3. `$RAW/standards/01_STANDARD.md` — the canonical `§`-section rules, fetched on demand when a step references a `§` you need to satisfy precisely.

**Faithful-fetch rule.** Use `curl -fsSL "<url>"` via Bash and read the saved file — this preserves the document verbatim, which matters most for `02_NEW_ADDON_CONTEXT.md` since you copy its contents into the new addon. Do **not** rely on WebFetch as the primary path: its summarizer rewrites and truncates content, so the context pack you drop in would be corrupted. WebFetch is a last-resort fallback only if `curl` is unavailable, and then treat its output as lossy. Save fetched docs under a scratch path (e.g. `/tmp` or the session scratchpad), then `Read` them.

**Hard stop.** If you cannot resolve `NEW_ADDON.md` **and** `standards/02_NEW_ADDON_CONTEXT.md` (no network, repo moved, 404), do not improvise a scaffold from memory. Stop and tell the user exactly which fetch failed and what you tried — the whole point is to be born compliant with the *current* standard.

## Step 1..N — Follow NEW_ADDON.md

Once fetched, **execute `NEW_ADDON.md`'s steps exactly as written**, scaffolding into a new `<AddonName>/` folder at cwd (bail with an error if it already exists). Do not restate or reinterpret them here — the fetched playbook is authoritative and may have evolved past this file. As of this writing it directs you to:

1. **Scaffold the skeleton** — the Ace3 stack (AceAddon registration, AceDB saved variables), the modular folder layout, MIT `LICENSE`, and an AceConsole slash command.
2. **Drop in the context pack** — put the *contents* of `standards/02_NEW_ADDON_CONTEXT.md` into the new addon's `docs/` as the full agent context, and leave a short root `CLAUDE.md` **stub** that points to it (§15). This is how the addon carries the standards in its memory: every future agent and contributor gets the complete brief with no external lookup.
3. **Pick a tier and lay out files** — Tier 1 (flat, ≤8 source files) for utilities, Tier 2 (modular: `core/ modules/ defaults/ settings/ locales/`) for multi-feature addons. Copy the vendored `libs/` set you actually `LibStub()` from an existing Ka0s addon so versions stay consistent.
4. **Fill in the starters** — TOC (fixed field order + `#`-section file listing), including the `## X-Standard:` line pointing at the standards repo; entry file, compat shims, locale, database/migrations, schema-driven settings, eager settings-category registration, debug console, message bus — from the context pack's starter snippets.
5. **Write tests first** — stand up the headless Lua 5.1 `tests/` harness and drive behavior test-first.
6. **Write the README to §15.1's canonical structure.**
7. **Check the Definition of Done** before tagging `v0.1.0`.
8. **Register in the roster** — add the addon's row to `standards/ADDONS.md` in the `WowAddonStandards` repo. Note that this edit is in a *different* repo; if you can't push there, tell the user this row still needs adding rather than silently skipping it.

Use the identity defaults from the playbook (Author `add1kted2ka0s` / Ka0s, MIT, Ace3, Retail-only single `## Interface:`, TOC `Title: Ka0s <Human Name>`, `<Addon>DB` saved-vars, 2–3 lowercase-char slash, PascalCase folder). Where the playbook says the context pack is the source of detail, read the snippet from the pack rather than inventing one.

If this list and the fetched `NEW_ADDON.md` ever disagree, **the fetched playbook wins**; where the playbook defers to `01_STANDARD.md` / the context pack, those win.

## After scaffolding, print

- The created file tree (just the paths), including `docs/` (the dropped-in context pack) and the root `CLAUDE.md` stub.
- The exact `## Interface:` value used and where it came from.
- The exact `## X-Standard:` URL written into the TOC.
- A reminder to run the packager (or fetch libs) before first use if `libs/` was left empty, and — if step 8's roster row could not be added from here — that `standards/ADDONS.md` still needs the new row.

Do not create `git init`, CI files, or hooks unless the user asks or the playbook requires them.

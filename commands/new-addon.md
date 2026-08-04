---
description: Scaffold a new Ka0s WoW addon that is born compliant with the Ka0s WoW Addon Standard. Fetches the NEW_ADDON.md playbook + the standards context pack from the WowAddonStandards repo at runtime and follows them to the letter — Ace3 skeleton, the modular layout, MIT, the root doc set (README.md, the CLAUDE.md stub, DEPENDENCIES.md), the canonical docs/ trio (ARCHITECTURE.md, testing.md, smoke-tests.md) and the first generated complexity report. The context pack is read at runtime and never written into the addon.
argument-hint: <AddonName> [one-line description]
allowed-tools: [Read, Glob, Grep, Bash, Write, WebFetch]
---

Scaffold a new WoW addon named **$ARGUMENTS** in the current working directory, **born compliant** with the Ka0s WoW Addon Standard. You do not carry the scaffolding rules yourself — the canonical rules and the new-addon procedure live in the `WowAddonStandards` repo and evolve there. Fetch the current playbook and context pack, then **follow them to the letter**.

**CRITICAL — the context pack is never stored in the addon.** You fetch `NEW_ADDON_CONTEXT.md` to a scratch path and build from it. Creating `docs/agent-context.md` — under that name or any other — is a compliance failure (`documentation-§3`, anti-pattern #49). The addon's `docs/` holds the canonical trio `ARCHITECTURE.md`, `testing.md` and `smoke-tests.md`, plus the four **required** topic-detail docs — the generated `test-cases.md`, `performance.md`, `perf-runs/README.md` and the generated `complexity.md` — and any further topic-detail docs the addon needs; the root `CLAUDE.md` stub is the repo's only agent brief.

## Standards source

The living standard lives at `https://github.com/tusharsaxena/WowAddonStandards`. Read its files from the raw base:

```
RAW=https://raw.githubusercontent.com/tusharsaxena/WowAddonStandards/master
```

## Step 0 — Resolve the playbook and the context pack (do this first)

Fetch these **faithfully** (see the fetch rule below), in order:

1. `$RAW/NEW_ADDON.md` — the new-addon playbook. It is authoritative for *how the addon is scaffolded*: its numbered steps (however many it now carries), the identity defaults, and the hard rules.
2. `$RAW/standards/NEW_ADDON_CONTEXT.md` — the full context pack: kickstart walkthrough, the modular starter tree, the starter snippets, hard-rules cheat sheet, and the Definition-of-Done checklist. It is the **source of detail** for every starter, including the setup files that wire the shared library modules — read the snippets from the pack rather than inventing them, and do not restate them here. **It is scaffolding you read, not a file you ship** — it is never written into the new addon (see the CRITICAL note above).
3. `$RAW/standards/STANDARDS.md` — the standard's **entry point / index**, fetched when a step references a rule you need to satisfy precisely. Follow its **Sections** list to the specific section file (`$RAW/standards/standards/<file>.md`) on demand. **Don't hard-code section filenames — discover them from the index.** The only fixed paths are `NEW_ADDON.md`, `standards/NEW_ADDON_CONTEXT.md`, and `standards/STANDARDS.md`; everything else you reach by following links, so the standard can be re-organized without changing this command.

**Faithful-fetch rule.** Use `curl -fsSL "<url>"` via Bash and read the saved file — this preserves the document verbatim, which matters most for `NEW_ADDON_CONTEXT.md` since you build the starters from its snippets verbatim. Do **not** rely on WebFetch as the primary path: its summarizer rewrites and truncates content, so the snippets you copy into code would be corrupted. WebFetch is a last-resort fallback only if `curl` is unavailable, and then treat its output as lossy. Save fetched docs under a scratch path (e.g. `/tmp` or the session scratchpad), then `Read` them.

**Hard stop.** If you cannot resolve `NEW_ADDON.md` **and** `standards/NEW_ADDON_CONTEXT.md` (no network, repo moved, 404), do not improvise a scaffold from memory. Stop and tell the user exactly which fetch failed and what you tried — the whole point is to be born compliant with the *current* standard.

**Referencing rule.** The standard cites sections as `filename-§N` (a whole section is its bare filename, e.g. `documentation`; a subsection is `documentation-§1`). Use that form; the retired global `§N.M` notation is gone.

## Step 1..N — Follow NEW_ADDON.md

Once fetched, **execute `NEW_ADDON.md`'s steps exactly as written**, scaffolding into a new `<AddonName>/` folder at cwd (bail with an error if it already exists). Do not restate or reinterpret them here — the fetched playbook is authoritative and may have evolved past this file. As of this writing it directs you to:

1. **Scaffold the skeleton** — the Ace3 stack (AceAddon registration, AceDB saved variables), the modular folder layout, MIT `LICENSE`, and an AceConsole slash command.
2. **Work from the context pack — never write it into the repo.** `standards/NEW_ADDON_CONTEXT.md` is *scaffolding*: read it from your scratch copy, build from it, and leave it there. Do **NOT** create `docs/agent-context.md` or any other stored copy of it (`documentation-§3`, anti-pattern #49) — every question it answers is answered the moment the addon exists, and a stored copy loads as *working context*, so a stale one gets **followed**. The addon's `docs/` carries the canonical trio — `ARCHITECTURE.md`, `testing.md`, `smoke-tests.md` — plus the four required topic-detail docs (`test-cases.md`, `performance.md`, `perf-runs/README.md`, `complexity.md`); the only agent brief in the repo is the short root `CLAUDE.md` **stub** (see `documentation`), with the durable per-addon context in `docs/ARCHITECTURE.md`, `docs/testing.md` and the root `DEPENDENCIES.md`. **Root ships exactly three docs plus `LICENSE`, and never a fourth: the full `README.md`, the `CLAUDE.md` stub, and `DEPENDENCIES.md`** — `DEPENDENCIES.md` is a **root** file, not a `docs/` member.
3. **Lay out files** — use the single modular layout (`core/ modules/ defaults/ settings/ locales/`) for every addon regardless of size (a small addon just has thin folders). Copy the vendored Ace3 `libs/` set you actually `LibStub()` from an existing Ka0s addon so versions stay consistent. Then vendor the **two Ka0s-owned payloads** from the `LibKa0s` repo itself — never from a sibling addon's copy, which may already have drifted:
   - its inner `LibKa0s/` folder → the new addon's `libs/LibKa0s/`, copied **whole**, and TOC-listed as the single aggregate `.xml` line the library ships. Copy every module, including ones the first release won't wire — a partial copy is the forbidden case, and it fails two ways: a module missing its dependency never registers at all (silently absent), while a module whose shell arrived without its attach file constructs fine and dies at **call** time, a panel build later.
   - its root-level `testkit/` folder → the new addon's `tests/_kit/`. It is a **sibling** of the ship folder, not inside it, and it goes under `tests/` — **never** `libs/`, which is the ship payload.
4. **Fill in the starters** — TOC (fixed field order + `#`-section file listing), including the `## X-Standard:` line pointing at the standards repo; entry file, compat shims, locale, database/migrations, schema-driven settings, and the message bus — from the context pack's starter snippets.

   **The shared subsystems are consumed, not written.** The prefixed chat printer, the debug console, the options panel toolkit, the slash dispatcher and the performance harness are `LibKa0s` modules. A new addon is born with **one setup file per adopted module**, and each holds exactly two things: a **descriptor** (the addon's seams into its own state — where a value lives, not how it looks) and a **degradation stub** for when the library is absent. Nothing else. Hand-building any of them — a private console, a private widget-maker set, a private dispatcher, a private test framework — is the forking anti-pattern the standard forbids outright, and so is patching the vendored copy instead of pushing an **additive** field upstream.

   The playbook names the setup files, their TOC positions and the descriptor fields each one carries, and the context pack carries the snippets. Follow those; don't reconstruct them from this file. Two invariants worth carrying into every one of them: each stub **MUST** answer every member the addon actually calls (a stub missing one is a crash moved to a rarer code path, not a fallback), and a stub **MUST NOT** re-implement the library's formatters, line formats, color codes or layout constants — that copy is the one that goes stale.
5. **Write tests first** — stand up `tests/` on the **vendored** `tests/_kit/` harness (thin extender over its base mock, load list derived from the TOC) and drive behavior test-first. Test what is **yours** — the descriptors, the degradation stubs, the addon's own logic — and do not re-test the library's internals; those cases live in the library repo, and a second copy is exactly the duplication this arrangement exists to remove.
6. **Write the README to `documentation-§1`'s canonical structure.**
7. **Write the root `DEPENDENCIES.md`** — the toolchain contract (`documentation-§7`). Every piece of software needed to build, run, test or release *this* addon, split **runtime (in-game) / development / release-and-assets**, each entry carrying the **evidence** for it (the TOC's dependency fields, a script's import, the command the harness runs) — never what a new addon usually needs, because one speculative entry costs the reader's trust in the whole list. Copy-pasteable WSL2 / Ubuntu install commands plus a one-line verification per tool. A new addon's honest runtime section is normally "World of Warcraft (Retail); nothing else", since every library is vendored. It answers *what to install*; `docs/testing.md` answers *how to verify* — point at it rather than restating it.
8. **Generate the first complexity report** — run the standard's exact invocation from the repo root and commit the result as `docs/complexity.md` with its generated-file header and a `## Watch list` (`performance-§10`), **before** tagging `v0.1.0`. Take the invocation from the fetched section rather than from memory; run it **verbatim**, because the report's whole value is that later releases can be diffed against this one. One file, overwritten in place at each release — never dated, never a directory — and never hand-edited. It is **not** a commit gate. If `lizard` is not installed, say so plainly and tell the user the report is still owed; do not fabricate one.
9. **Check the Definition of Done** before tagging `v0.1.0`.
10. **Register in the roster** — add the addon's row to `standards/ADDONS.md` in the `WowAddonStandards` repo. Note that this edit is in a *different* repo; if you can't push there, tell the user this row still needs adding rather than silently skipping it.

Use the identity defaults from the playbook (Author `add1kted2ka0s` / Ka0s, MIT, Ace3, Retail-only single `## Interface:`, TOC `Title: Ka0s <Human Name>`, `<Addon>DB` saved-vars, 2–3 lowercase-char slash, PascalCase folder). Where the playbook says the context pack is the source of detail, read the snippet from the pack rather than inventing one.

If this list and the fetched `NEW_ADDON.md` ever disagree, **the fetched playbook wins**; where the playbook defers to `STANDARDS.md` (and its section files) / the context pack, those win.

## After scaffolding, print

- The created file tree (just the paths), including the **root** doc set — `README.md`, the `CLAUDE.md` stub and `DEPENDENCIES.md`, plus `LICENSE`, and nothing else at root — `docs/` (the trio — ARCHITECTURE.md, testing.md, smoke-tests.md — and the four required topic-detail docs: test-cases.md, performance.md, perf-runs/README.md, complexity.md; **no** agent-context.md), the vendored `libs/LibKa0s/`, and `tests/_kit/`.
- **Whether `docs/complexity.md` was actually generated**, and by which invocation — or, if `lizard` was absent, that the report is still owed and the addon must not be tagged until it exists.
- **Which `LibKa0s` modules the scaffold wired** (one setup file each) versus which were vendored but not yet wired — adoption is per module and on the addon's own schedule, so "vendored, not wired" is a normal state, not an omission. Say where each payload was copied **from** (the `LibKa0s` repo, not a sibling addon) so the provenance is on the record.
- The exact `## Interface:` value used and where it came from.
- The exact `## X-Standard:` URL written into the TOC.
- A reminder to run the packager (or fetch libs) before first use if `libs/` was left empty, and — if step 8's roster row could not be added from here — that `standards/ADDONS.md` still needs the new row.

Do not create `git init`, CI files, or hooks unless the user asks or the playbook requires them.

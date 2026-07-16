# CLAUDE.md — wow-addon plugin

## Purpose & stack

A **Claude Code plugin** (not a WoW addon itself) that ships helpers for World of Warcraft addon development: standard-compliant scaffolding, compliance auditing, interface/version bumping, doc sync, test-battery running, GitHub issue listing/creation, git diff/commit, a CRLF hook, and a WoW-specific review subagent. Everything here is **Markdown command/agent specs + one Bash hook script + JSON manifests** — there is no compiled code and no test suite.

Current version: **1.7.2** (in `.claude-plugin/plugin.json`).

## Module/package map

- `.claude-plugin/plugin.json` — plugin manifest; **the single source of truth for the version**.
- `.claude-plugin/marketplace.json` — marketplace entry; carries a **mirror of the description** (no version field of its own).
- `commands/*.md` — 11 slash-command specs (`/wow-addon:<name>`), each also invocable as a Skill of the same name. Two of them (`review.md`, `standards-audit.md`) are thin **wrappers that dispatch to the subagent of the same name**; the other nine act directly.
- `agents/*.md` — 2 subagent specs: `review` (WoW-specific principal-level review → `docs/reviews/<date>/`; also fetches the standard to keep its own remediation compliant, but does **not** audit) and `standards-audit` (read-only compliance audit → `docs/audits/<date>/`).
- `hooks/hooks.json` + `scripts/normalize-crlf.sh` — the CRLF-normalization hook.
- `README.md` — user-facing docs. `LICENSE` — MIT.

## Entry points & lifecycle

Claude Code auto-discovers `commands/` and `agents/` by directory; there is no registration file listing them. A command file becomes live the moment it exists and the plugin is (re)loaded. `hooks/hooks.json` registers the `PostToolUse` hook. To activate changes in a session: **`/reload-plugins`** (no restart needed).

- **Command spec** = YAML frontmatter (`description`, `argument-hint`, `allowed-tools`) + a Markdown body that instructs the agent. `$ARGUMENTS` is the user's argument string.
- **Agent spec** = frontmatter (`name`, `description`, `tools`) + body. The `name` becomes `wow-addon:<name>` when dispatched.

## Configuration & env

None. No env vars, no config files, no persistent state. Some specs need external tools **on the machine of whoever runs them** (still not local plugin config): `standards-audit` and `new-addon` fetch the external **[`WowAddonStandards`](https://github.com/tusharsaxena/WowAddonStandards)** repo at runtime (raw GitHub, needs network); `fetch-issues` and `add-issue` shell out to the **`gh`** CLI (must be installed and authenticated); `run-tests` invokes whatever it finds — **luacheck** and a **Lua** interpreter — treating an absent tool as a skipped suite, not a failure.

## Build / test / run

- **No build, no tests.** Validation is: `python3 -c "import json; ..."` on the two manifests, and a manual `/reload-plugins` to confirm the plugin loads (`Reloaded: … plugins · … skills · … agents · … hooks`).
- The CRLF hook script is Bash; there's no harness for it beyond running the flow that triggers `Write|Edit|MultiEdit` inside a repo whose `.gitattributes` declares `eol=crlf`.

## Conventions & hot zones (footguns)

- **Adding/removing a command or agent is a 4-touch change.** Keep these in sync or the docs drift:
  1. the `commands/*.md` or `agents/*.md` file,
  2. the README table (Commands / Subagents),
  3. **both** manifest descriptions (`plugin.json` + `marketplace.json`),
  4. the version in `plugin.json` (bump it).
- **Command wrappers for subagents** (`review`, `standards-audit`) are documented under **Subagents** in the README, not the Commands table — follow that taxonomy for any future wrapper.
- **Runtime-fetch specs** (`standards-audit`, `new-addon`, and — for its guardrail only — `review`): fetch the playbook + standard with `curl -fsSL` (verbatim); WebFetch is a **lossy fallback only** — its summarizer mangles verbatim content. If the standard can't be resolved: `standards-audit`/`new-addon` must **hard-stop** (their whole output is worthless without it), but `review` must **degrade gracefully** — it fetches the standard only to keep its own remediation compliant, so on failure it proceeds with the review and notes that the standards cross-check was skipped. Don't "fix" `review` to hard-stop.
- **Hard-code only the entry points; discover the rest by following links.** The standard is **split** — `standards/STANDARDS.md` is an index whose **Sections** list links one file per section under `standards/standards/`. Specs fetch `STANDARDS.md` and then **every section file it lists**; they **must not** hard-code section filenames, so the standard can be re-organized upstream without touching this plugin. The only fixed remote paths are the playbooks (`AUDIT.md`/`NEW_ADDON.md`), `standards/STANDARDS.md`, and `standards/NEW_ADDON_CONTEXT.md` (dropped verbatim into new addons).
- **Reference the standard's sections as `filename-§N`.** A whole section is its bare filename (`architecture`, `anti-patterns`); a subsection is `filename-§N` (`architecture-§5`, `documentation-§1`), the number being that section's **local** count. The old global `§N.M` notation is retired — don't use or reintroduce it in specs or artifacts.
- **`standards-audit` is read-only** on the audited addon — it only writes under `docs/audits/<date>/`. Don't let it edit addon code.
- **Commit style:** terse capitalized imperative subjects, no Conventional-Commits prefix; releases commit **directly to `master`**; commits carry a `Co-Authored-By: Claude …` trailer (match the recent `git log`).

## Known TODOs

None tracked. (The `TODO/FIXME` strings that appear in `commands/diff.md` and `commands/sync-docs.md` are those specs *describing their own behavior*, not project TODOs.)

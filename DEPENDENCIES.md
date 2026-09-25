# DEPENDENCIES.md — wow-addon

The toolchain contract for **this** repository (documentation-§7).

> **Read this first.** This is a **documentation-and-tooling repo** (`documentation-§8`), not an
> addon: no `.toc`, no Lua, no `libs/`, no `tests/` harness, nothing that loads in the WoW client.
> `documentation-§7` still binds, but it is read for that repo kind — a short **required** list, an
> explicit **not used here** list with reasons, and no invented rows. Every entry below names the
> `file:line` in *this* tree that needs it; an entry with no such line does not belong here.
>
> The repo is 40 tracked files: 28 Markdown (the command and agent specs), three JSON manifests,
> two Python files, two Bash scripts, the extensionless `scripts/ka0s-bounded` and its POSIX `sh`
> exec wrapper `bin/ka0s-bounded` (what puts the bare name on the plugin's PATH entry), plus `LICENSE`,
> `.gitattributes` and `.gitignore`. Line endings are **LF** here, not the CRLF the client-bound
> addon repos pin.

## The short version

Clone it, then point Claude Code at it as a plugin. There is no build step and no package manifest —
the two Python files are standard-library-only and the shell scripts are Bash, apart from the
one-line POSIX `sh` wrapper `bin/ka0s-bounded`, which only `exec`s the Bash runner.

```sh
git clone https://github.com/tusharsaxena/wow-addon.git
cd wow-addon
python3 scripts/test_bounded_runs.py    # the repo's only test
```

## Runtime — what the plugin's hooks need on the machine running Claude Code

These run on every Bash call and every file write, so an absence here is felt immediately. All five
ship with a stock WSL2 Ubuntu install; none needs a language package manager.

| Software | Package manager | Why this repo needs it | Evidence | Install (WSL2 / Ubuntu) | Verify |
|---|---|---|---|---|---|
| **bash** ≥ 4.2 | `apt` (`bash`) | Both hooks are invoked as `bash <script>`, and `scripts/ka0s-bounded` uses Bash-only syntax (arrays, `exec {fd}>`). | `hooks/hooks.json:9`, `hooks/hooks.json:20`; `scripts/ka0s-bounded:1`, `:78`, `:105` | preinstalled; `sudo apt update && sudo apt install -y bash` | `bash --version` |
| **python3** ≥ 3.8 | `apt` (`python3`) | The PreToolUse guard is a Python script, and the PostToolUse hook shells out to `python3 -c` to parse the hook's JSON payload. Standard library only — `json`, `os`, `re`, `shlex`, `sys`. | `scripts/bounded_runs.py:1`, `:27-31`; `scripts/bounded-runs-hook.sh:30`; `scripts/normalize-eol.sh:15` | `sudo apt install -y python3` | `python3 --version` |
| **git** ≥ 2.34 | `apt` (`git`) | The line-ending hook asks git — and only git — what a written file's declared ending is: `git rev-parse --show-toplevel` to find the repo, then `git check-attr text eol` to read `.gitattributes`. | `scripts/normalize-eol.sh:36`, `:52` | `sudo apt install -y git` | `git --version` |
| **perl** ≥ 5.10 | `apt` (`perl`) | The same hook does the byte rewrite in perl rather than sed, deliberately, because BSD and GNU `sed -i` differ. Both the CRLF and the LF branch use it. | `scripts/normalize-eol.sh:63`, `:68`, `:76` | preinstalled; `sudo apt install -y perl` | `perl --version` |
| **coreutils** (`timeout`) ≥ 8.30 | `apt` (`coreutils`) | `ka0s-bounded`'s wall-clock bound is `timeout --foreground -k 10`. It is probed with `command -v`, so an absence drops that one bound rather than failing the run. | `scripts/ka0s-bounded:98-99` | preinstalled; `sudo apt install -y coreutils` | `timeout --version` |

## Runtime — optional, and degraded gracefully when absent

`ka0s-bounded` probes each of these and drops the bound it provides rather than refusing to run. They
are listed because losing one silently weakens the guard the whole repo exists to enforce.

| Software | Package manager | Why this repo needs it | Evidence | Install (WSL2 / Ubuntu) | Verify |
|---|---|---|---|---|---|
| **util-linux** (`flock`) | `apt` (`util-linux`) | The machine-wide slot pool, so several repos and agents can start bounded runs in parallel without piling onto the same RAM. | `scripts/ka0s-bounded:65`, `:79` | preinstalled; `sudo apt install -y util-linux` | `flock --version` |
| **systemd** (`systemd-run`) | `apt` (`systemd`) | The process-*tree* memory cap — a transient `--user --scope` with `MemoryMax`, `MemorySwapMax=0` and `TasksMax`, so a runaway runner is killed as one unit instead of by the kernel choosing among everything on the machine. Needs a user session bus; skipped where there is none. | `scripts/ka0s-bounded:103-106` | preinstalled on systemd WSL2; `sudo apt install -y systemd` | `systemd-run --version` |

## Development — what you need to change this repo

| Software | Package manager | Why this repo needs it | Evidence | Install (WSL2 / Ubuntu) | Verify |
|---|---|---|---|---|---|
| **python3** (with `unittest`) | `apt` (`python3`) | The repo's only test file. Run it after touching either bounded-runs file. | `scripts/test_bounded_runs.py:1-13`; `CLAUDE.md:41` | `sudo apt install -y python3` | `python3 scripts/test_bounded_runs.py` |
| **git** | `apt` (`git`) | `.gitattributes` pins this repo to **LF**. `git check-attr` is the only correct reader of that pin. | `.gitattributes`; `scripts/normalize-eol.sh:52` | `sudo apt install -y git` | `git check-attr text eol -- CLAUDE.md` |
| **Claude Code** | its own installer | The specs in `commands/` and `agents/` are only executable as plugin slash commands and subagents; `/reload-plugins` is the load check. | `.claude-plugin/plugin.json`; `CLAUDE.md:5` | see the Claude Code docs | `/reload-plugins` in a session |

## Required on the machine of whoever *runs* a command (not of this repo)

Several specs shell out. These are not dependencies of this tree — nothing here imports or invokes
them — but a command will report a skip or a stall without them, so they are named once.

| Software | Package manager | Which specs need it | What happens without it |
|---|---|---|---|
| **`gh`** (GitHub CLI), authenticated | `apt` (`gh`, from the GitHub apt repository) | the six `issue-*` commands, `harvest-standards`, `revendor-libka0s`'s decline filing, the `standards-audit` agent's register read | `issue-audit` treats it as a skipped sweep; the others report an unfiled write rather than degrading silently (`CLAUDE.md:70`, `CLAUDE.md:69`) |
| **network access to raw GitHub** | — | `standards-audit`, `new-addon`, `revendor-standards`, `automated-tests`, `perf-analysis` fetch the `WowAddonStandards` playbooks at runtime | the command cannot start; it says so rather than working from memory (`CLAUDE.md:52`) |
| **sibling checkouts on local disk** | — | `revendor-libka0s` reads `../LibKa0s` at a git tag; `harvest-standards` reads every addon repo and the standards working tree | reported as not run, never inferred (`commands/revendor-libka0s.md`, `commands/harvest-standards.md`) |
| **Lua 5.1**, **luacheck**, **lizard** | `apt` (`lua5.1`), `luarocks` (`luacheck`), `pipx` (`lizard`; bare `pip` fails on Ubuntu 24.04's PEP 668 marker) | `run-tests`, `review`, `bump-version`, `standards-audit`, `automated-tests` — all of which execute **inside an addon repo**, never here | a **stated skip** / *not run*, never an inferred pass and never a fabricated number (`CLAUDE.md:60`, `CLAUDE.md:59`) |

## Not used here, and why

Listed so a reader arriving from an addon's `DEPENDENCIES.md` can tell "not installed" from "not
applicable".

| Software | Status | Why |
|---|---|---|
| **Lua 5.1** | **not used here** | No `.lua` file is tracked in this repo. The Lua the specs talk about runs in the addon repo the command is invoked from. |
| **luacheck** | **not used here** | Lint needs Lua to lint, and there is no `.luacheckrc`. |
| **lizard** | **not used here** | Cyclomatic complexity over zero Lua functions is not a measurement. The two Python files and four shell scripts are on no complexity gate. |
| **A WoW client** | **not used here** | Nothing here loads as an addon; there is no `.toc` and no `docs/smoke-tests.md`. |
| **pip / a `requirements.txt`** | **not used here** | `bounded_runs.py` and `test_bounded_runs.py` import only the standard library (`json`, `os`, `re`, `shlex`, `sys`, `subprocess`, `tempfile`, `unittest`). Adding a manifest would be the first thing to go stale. |
| **packager / release tooling** | **not used here** | No `.pkgmeta` and no artifact to publish. The plugin is consumed from the repo by Claude Code, not released as a build. |

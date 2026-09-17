#!/usr/bin/env python3
"""wow-addon plugin: PreToolUse(Bash) guard that refuses unbounded heavy test runs.

A heavy run is `lua tests/run.lua`, `lua tests/perf.lua`, `run-automated-tests.sh`, `luacheck` or
`lizard`. One of those, run unbounded, once took a WSL2 VM and the Claude Code session driving it
down (a runner that re-launched itself without end). The fix lives in two places: LibKa0s' test kit
(revision 23) bounds its own Lua runs, and `scripts/ka0s-bounded` bounds anything. This hook is the
backstop that works even when no memory rule or skill text reached the session: it denies the
command and names the wrapper to prefix.

A segment passes when:
  * its command is `ka0s-bounded` (by any path), or
  * it is already bounded by hand: a `timeout` wrapper AND a `ulimit -v` earlier in the same command, or
  * it carries `KA0S_BOUNDED_HOOK=off` as an inline assignment (a deliberate, visible opt-out), or
  * it is a Lua run of `tests/run.lua` / `tests/perf.lua` in a repo whose vendored kit is revision
    23 or newer: that kit re-launches itself under the same bounds (depth, tree memory, process
    memory, wall clock), so the wrapper would only add the slot pool, or
  * it is plainly not a run: `luacheck --version`, `lizard --help`, and any command where the words
    only appear as arguments (`grep lua tests/run.lua`, `git diff tests/run.lua`).

The matcher is deliberately a shell-ish tokenizer, not a shell parser: it splits on the control
operators, drops leading assignments and transparent wrappers (`env`, `time`, `nice`, `exec`,
`command`, `timeout …`), and looks at the first real word. False negatives on exotic shell are
acceptable; false positives on ordinary commands are not.
"""

import json
import os
import re
import shlex
import sys

WRAPPER = "ka0s-bounded"
LUA_INTERPRETERS = {"lua", "lua5.1", "luajit", "lua5.2", "lua5.3", "lua5.4"}
SHELLS = {"bash", "sh", "zsh", "dash"}
TRANSPARENT = {"env", "time", "nice", "exec", "command", "nohup", "stdbuf", "ionice"}
INFO_FLAGS = {"--version", "-v", "--help", "-h"}
LUA_RUNNERS = ("tests/run.lua", "tests/perf.lua")
KIT_MIN_REVISION = 23

SPLIT = re.compile(r"\|\||&&|;|\||&|\n|\$\(|`|\(|\)|\{|\}")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def tokens(segment):
    try:
        return shlex.split(segment, comments=True)
    except ValueError:
        return segment.split()


def strip_prefix(words):
    """Drop assignments and transparent wrappers. Returns (words, assignments, timed)."""
    assignments = {}
    timed = False
    i = 0
    while i < len(words):
        w = words[i]
        if ASSIGNMENT.match(w):
            k, _, v = w.partition("=")
            assignments[k] = v
            i += 1
        elif w in TRANSPARENT:
            i += 1
            # `env -i`, `nice -n 5`, `stdbuf -oL`: skip their options
            while i < len(words) and words[i].startswith("-"):
                i += 1
                if i < len(words) and words[i - 1] in ("-n", "-u") and not words[i].startswith("-"):
                    i += 1
        elif w == "timeout":
            timed = True
            i += 1
            while i < len(words) and words[i].startswith("-"):
                opt = words[i]
                i += 1
                if opt in ("-k", "-s", "--kill-after", "--signal") and i < len(words):
                    i += 1
            if i < len(words):
                i += 1  # the duration
        else:
            break
    return words[i:], assignments, timed


def kit_revision(repo_root):
    try:
        with open(os.path.join(repo_root, "tests", "_kit", "framework.lua"), encoding="utf-8",
                  errors="replace") as f:
            m = re.search(r"Kit\.VERSION\s*=\s*(\d+)", f.read(8192 * 4))
            return int(m.group(1)) if m else None
    except OSError:
        return None


def heavy(words, cwd):
    """The kind of heavy run `words` starts, or None. `cwd` resolves a Lua runner's repo."""
    if not words:
        return None
    name = os.path.basename(words[0])
    args = words[1:]

    if name == WRAPPER:
        return None

    if name in SHELLS and args:
        script = next((a for a in args if not a.startswith("-")), None)
        if script and os.path.basename(script) == "run-automated-tests.sh":
            return "run-automated-tests.sh"
        return None

    if name == "run-automated-tests.sh":
        return "run-automated-tests.sh"

    if name in ("luacheck", "lizard"):
        if args and all(a in INFO_FLAGS for a in args):
            return None
        return name

    if name in LUA_INTERPRETERS:
        script = next((a for a in args if not a.startswith("-")), None)
        if not script:
            return None
        norm = script.replace("\\", "/")
        for runner in LUA_RUNNERS:
            if norm == runner or norm.endswith("/" + runner):
                prefix = norm[: -len(runner)].rstrip("/")
                root = prefix if os.path.isabs(prefix) else os.path.join(cwd, prefix)
                rev = kit_revision(os.path.normpath(root or cwd))
                if rev is not None and rev >= KIT_MIN_REVISION:
                    return None
                return "lua " + runner
        return None

    return None


def check(command, cwd):
    """The heavy runs in `command` that are not bounded, as a list of kinds."""
    bounded_by_hand = re.search(r"\bulimit\s+(-[A-Za-z]*v|-v)\b", command) is not None
    found = []
    here = cwd
    for segment in SPLIT.split(command):
        words = tokens(segment.strip())
        if not words:
            continue
        rest, assignments, timed = strip_prefix(words)
        if not rest:
            continue
        if rest[0] == "cd" and len(rest) > 1:
            target = os.path.expanduser(rest[1])
            here = target if os.path.isabs(target) else os.path.normpath(os.path.join(here, target))
            continue
        if assignments.get("KA0S_BOUNDED_HOOK") == "off":
            continue
        kind = heavy(rest, here)
        if kind is None:
            continue
        if timed and bounded_by_hand:
            continue
        found.append(kind)
    return found


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in (None, "Bash"):
        return 0
    command = (data.get("tool_input") or {}).get("command") or ""
    cwd = data.get("cwd") or os.getcwd()
    found = check(command, cwd)
    if not found:
        return 0

    wrapper = os.path.expanduser("~/.claude/wow-addon/bin/" + WRAPPER)
    kinds = ", ".join(sorted(set(found)))
    reason = (
        f"Unbounded heavy run ({kinds}). Prefix it with the bounded runner: `{wrapper} <command>` "
        f"-- e.g. `{wrapper} lua tests/run.lua`. It caps process memory, the process tree's memory "
        "and wall-clock time, and queues on a machine-wide slot pool, so running several repos' "
        "suites in parallel is fine. An unbounded runaway suite once OOM-killed the whole WSL VM "
        "and this session with it. A repo whose tests/_kit is revision 23+ self-bounds its Lua runs "
        "and is not stopped here. Deliberate opt-out: an inline KA0S_BOUNDED_HOOK=off assignment."
    )
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())

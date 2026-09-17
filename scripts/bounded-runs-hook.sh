#!/usr/bin/env bash
# wow-addon plugin: PreToolUse(Bash) hook -- refuse unbounded heavy test runs.
#
# Two jobs, both cheap:
#   1. Keep a stable path to the bounded runner: ~/.claude/wow-addon/bin/ka0s-bounded is a symlink to
#      this plugin version's scripts/ka0s-bounded, refreshed whenever it points anywhere else (a
#      plugin update moves the cache directory). Specs and the refusal message name that path.
#   2. Hand the command to scripts/bounded_runs.py, which denies a heavy run that is not bounded.
#
# Fails open: any error here exits 0 with no output, so a broken hook can never block Bash.

set -u

root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)}"

link_dir="$HOME/.claude/wow-addon/bin"
target="$root/scripts/ka0s-bounded"
if [ -f "$target" ] && [ "$(readlink "$link_dir/ka0s-bounded" 2>/dev/null)" != "$target" ]; then
    mkdir -p "$link_dir" 2>/dev/null && ln -sfn "$target" "$link_dir/ka0s-bounded" 2>/dev/null
fi

input="$(cat 2>/dev/null || true)"

# Fast path: nothing that could be a heavy run.
case "$input" in
    *lua*|*luacheck*|*lizard*|*run-automated-tests*) ;;
    *) exit 0 ;;
esac

printf '%s' "$input" | python3 "$root/scripts/bounded_runs.py" 2>/dev/null || true
exit 0

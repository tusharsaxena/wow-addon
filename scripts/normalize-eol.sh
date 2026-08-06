#!/usr/bin/env bash
# wow-addon plugin: normalize a just-written file to whatever line ending its repo's
# .gitattributes declares for it — CRLF in a client-bound Ka0s repo, LF in one that ships
# nothing to the WoW client (Ka0s WoW Addon Standard, line-endings-§2).
# Triggered by a PostToolUse hook on Write|Edit|MultiEdit.
# Silent on success and on non-applicable files. Never errors out — exit 0 unconditionally so it can't block writes.

set -u

input="$(cat 2>/dev/null || true)"

# Extract the file path from the hook input. Try common shapes.
# NOTE: use `python3 -c` (not a heredoc) — a heredoc inside $(...) trips a bash
# command-substitution parse bug at runtime ("syntax error near unexpected token `||'").
file_path="$(printf '%s' "$input" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input") or {}
tr = d.get("tool_response") or {}
# Common keys across Claude Code versions
for key in ("file_path", "filePath", "path"):
    v = ti.get(key) or tr.get(key)
    if v:
        print(v)
        sys.exit(0)
' 2>/dev/null || true)"

[[ -z "$file_path" ]] && exit 0
[[ ! -f "$file_path" ]] && exit 0

# Resolve the file's repo root (if any). No repo → nothing to do.
file_dir="$(dirname -- "$file_path")"
repo_root="$(git -C "$file_dir" rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "$repo_root" ]] && exit 0

# Compute path relative to repo root for git check-attr.
abs_file="$(cd "$file_dir" && pwd)/$(basename -- "$file_path")"
rel_path="${abs_file#"$repo_root"/}"

# Ask git what eol attribute applies to this file per .gitattributes.
# `crlf` and `lf` are the two the Ka0s standard declares (line-endings-§2); anything else —
# unspecified, unset, a path marked binary — is not ours to touch and exits silently.
eol_attr="$(git -C "$repo_root" check-attr eol -- "$rel_path" 2>/dev/null | awk -F': ' '{print $NF}')"

case "$eol_attr" in
    crlf)
        # Already fully CRLF? Bail. The fast path has to ask "is any line ending bare?",
        # not "is any line ending CRLF?" — the latter passes a mixed file that is still
        # half wrong, which is exactly what an Edit into a CRLF file produces.
        if LC_ALL=C perl -0777 -ne 'exit(/(?<!\r)\n/ ? 1 : 0)' -- "$file_path" 2>/dev/null; then
            exit 0
        fi
        # Normalize LF → CRLF. perl, for reliability across BSD/GNU sed differences.
        # Only convert lone \n; leave existing \r\n alone.
        perl -i -pe 's/(?<!\r)\n/\r\n/g' -- "$file_path" 2>/dev/null || true
        ;;
    lf)
        # Mirror of the above, and deliberately NOT the same test: a file with no CR is
        # done here and unfinished there, so the two fast paths cannot be shared.
        if ! LC_ALL=C grep -q $'\r' -- "$file_path" 2>/dev/null; then
            exit 0
        fi
        perl -i -pe 's/\r\n/\n/g; s/\r/\n/g' -- "$file_path" 2>/dev/null || true
        ;;
esac

exit 0

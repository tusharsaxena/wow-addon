#!/usr/bin/env bash
# wow-addon plugin: normalize a just-written file to CRLF if its repo's .gitattributes declares CRLF for it.
# Triggered by a PostToolUse hook on Write|Edit|MultiEdit.
# Silent on success and on non-applicable files. Never errors out — exit 0 unconditionally so it can't block writes.

set -u

input="$(cat 2>/dev/null || true)"

# Extract the file path from the hook input. Try common shapes.
file_path="$(printf '%s' "$input" | python3 - <<'PY' 2>/dev/null || true
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
PY
)"

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
eol_attr="$(git -C "$repo_root" check-attr eol -- "$rel_path" 2>/dev/null | awk -F': ' '{print $NF}')"
[[ "$eol_attr" != "crlf" ]] && exit 0

# File already CRLF? Bail. (Check: does any line end with \r\n?)
if LC_ALL=C grep -q $'\r$' -- "$file_path" 2>/dev/null; then
    exit 0
fi

# Normalize LF → CRLF. Use perl for reliability across BSD/GNU sed differences.
# Only convert lone \n; leave existing \r\n alone.
perl -i -pe 's/(?<!\r)\n/\r\n/g' -- "$file_path" 2>/dev/null || true

exit 0

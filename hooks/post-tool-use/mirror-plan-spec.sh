#!/usr/bin/env bash
# PostToolUse hook (Write|Edit) for the checklist-system plugin.
#
# Policy (2026-06-12): whenever a plan or spec file is written or substantively
# updated for slice-tracked work, mirror it to the Linear slice. This hook
# detects Write/Edit on docs/superpowers/{plans,specs}/*.md inside a directory
# governed by .checklist.json and injects a reminder to mirror the content to
# the current slice via linear.py set-body (preserving the checkbox section).
#
# Silent (exit 0, no output) when the file is not a plan/spec or no
# .checklist.json governs it.

set -u

INPUT="$(cat)"

python3 - "$INPUT" <<'PYEOF'
import json, os, sys

try:
    payload = json.loads(sys.argv[1])
except (IndexError, json.JSONDecodeError):
    sys.exit(0)

tool_input = payload.get("tool_input") or {}
file_path = tool_input.get("file_path") or ""
if not file_path:
    sys.exit(0)

norm = file_path.replace(os.sep, "/")
if "/docs/superpowers/plans/" not in norm and "/docs/superpowers/specs/" not in norm:
    sys.exit(0)
if not norm.endswith(".md"):
    sys.exit(0)

# Walk up from the file looking for .checklist.json (stop at $HOME, like the
# SessionStart hook does).
home = os.path.expanduser("~")
d = os.path.dirname(os.path.abspath(file_path))
config = None
while d and d != "/" and d != home:
    candidate = os.path.join(d, ".checklist.json")
    if os.path.isfile(candidate):
        config = candidate
        break
    d = os.path.dirname(d)
if config is None:
    sys.exit(0)

try:
    with open(config) as f:
        slice_issue = (json.load(f) or {}).get("current_slice_issue") or "the current slice"
except (OSError, json.JSONDecodeError):
    slice_issue = "the current slice"

kind = "plan" if "/plans/" in norm else "spec"
context = (
    f"[checklist-mirror] A {kind} file for slice-tracked work was just written/updated: "
    f"{file_path}. STANDING POLICY: whenever a plan or spec file is written or "
    f"substantively updated for slice-tracked work, mirror it to the Linear slice that "
    f"tracks that work. The configured current slice is {slice_issue} (config: {config}), "
    f"but verify it is the slice this {kind} belongs to before posting. Before the end of "
    f"this task, mirror the content into the slice body via "
    f"the checklist plugin's `linear.py set-body <SLICE> ...` wrapper "
    f"-- preserving the top checkbox section (see the 'Slice body structure' spec doc). "
    f"Skip only if this edit was trivial (typo/formatting) or you already mirrored this "
    f"file's current content this session."
)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": context,
    }
}))
PYEOF
exit 0

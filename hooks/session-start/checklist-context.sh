#!/usr/bin/env bash
# SessionStart hook for the checklist-system plugin.
#
# Behavior:
#   - Walks up from CWD looking for .checklist.json (stops at $HOME).
#   - If not found, prints nothing — the system silently doesn't apply.
#   - If found, prints the .checklist.json contents + the Checklist System
#     spec (a static bundle shipped with the plugin) as session context.
#
# The spec is bundled at $CLAUDE_PLUGIN_ROOT/spec/ so the system works with no
# access to any private Linear workspace. A Linear API key (see scripts/linear.py)
# is only needed for the actual slice operations, not to load the spec.

set -u

find_checklist() {
  local dir
  dir="$(pwd)"
  while [ "$dir" != "/" ] && [ "$dir" != "$HOME" ]; do
    if [ -f "$dir/.checklist.json" ]; then
      echo "$dir/.checklist.json"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  if [ -f "$HOME/.checklist.json" ]; then
    echo "$HOME/.checklist.json"
    return 0
  fi
  return 1
}

CHECKLIST_FILE="$(find_checklist)" || exit 0

LINEAR_PY="${CLAUDE_PLUGIN_ROOT}/scripts/linear.py"

echo "# Checklist System: active in this directory"
echo
echo "Found \`.checklist.json\` at \`${CHECKLIST_FILE}\`:"
echo
echo '```json'
cat "$CHECKLIST_FILE"
echo
echo '```'
echo

# Seed the statusline progress cache (.checklist.state.json) so the status bar
# shows the current slice's completion from the first render. Best-effort, silent.
SLICE_ID="$(jq -r '.current_slice_issue // empty' "$CHECKLIST_FILE" 2>/dev/null)"
if [ -n "$SLICE_ID" ]; then
  python3 "$LINEAR_PY" sync-slice-state "$SLICE_ID" "$(dirname "$CHECKLIST_FILE")" >/dev/null 2>&1 || true
fi

echo "## Spec"
echo
SPEC_FILE="${CLAUDE_PLUGIN_ROOT}/spec/index.md"
if [ -f "$SPEC_FILE" ]; then
  cat "$SPEC_FILE"
else
  echo "_Spec bundle missing at \`\$CLAUDE_PLUGIN_ROOT/spec/index.md\` — reinstall the plugin._"
fi

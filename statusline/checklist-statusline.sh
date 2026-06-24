#!/bin/sh
# Optional Claude Code status-line widget for the checklist plugin.
#
# Shows the current slice's progress, e.g.  ABC-123 ▰▰▰▱▱▱▱ 3/7  — read from the
# local .checklist.state.json cache the plugin maintains (zero network, pure file
# read). Falls back to the current folder's name when no slice governs the cwd.
#
# This is OPTIONAL and self-contained. To enable it, point statusLine.command at
# this file in your Claude Code settings.json — see the README "Status bar widget".
#
# Requires: jq (already used by the plugin's hook).

input=$(cat 2>/dev/null)

cwd=""
if command -v jq >/dev/null 2>&1; then
  cwd=$(printf '%s' "$input" | jq -r '.workspace.current_dir // .cwd // ""' 2>/dev/null)
fi
[ -z "$cwd" ] && cwd="$PWD"
folder=$(basename "$cwd")

# Walk up from cwd to $HOME for the governing .checklist.json (same rule the system uses).
checklist_dir=""
dir="$cwd"
while [ -n "$dir" ] && [ "$dir" != "/" ]; do
  if [ -f "$dir/.checklist.json" ]; then checklist_dir="$dir"; break; fi
  [ "$dir" = "$HOME" ] && break
  dir=$(dirname "$dir")
done

slot="$folder"
if [ -n "$checklist_dir" ] && command -v jq >/dev/null 2>&1; then
  cur=$(jq -r '.current_slice_issue // empty' "$checklist_dir/.checklist.json" 2>/dev/null)
  state_file="$checklist_dir/.checklist.state.json"
  if [ -n "$cur" ] && [ -f "$state_file" ]; then
    s=$(jq -r '.slice // empty' "$state_file" 2>/dev/null)
    d=$(jq -r '.done // empty' "$state_file" 2>/dev/null)
    t=$(jq -r '.total // empty' "$state_file" 2>/dev/null)
    if [ "$s" = "$cur" ] && [ -n "$t" ] && [ "$t" -gt 0 ] 2>/dev/null; then
      filled=$(( (d * 7 + t / 2) / t ))
      [ "$filled" -lt 0 ] && filled=0
      [ "$filled" -gt 7 ] && filled=7
      bar=""; i=0
      while [ "$i" -lt 7 ]; do
        if [ "$i" -lt "$filled" ]; then bar="${bar}▰"; else bar="${bar}▱"; fi
        i=$((i + 1))
      done
      slot="${cur} ${bar} ${d}/${t}"
    fi
  fi
fi

# Red, matching the maintainer's slice slot. Drop the escape codes for plain text.
printf '\033[91m%s\033[0m' "$slot"

---
name: new
description: Add a checklist item to the current slice (a Linear slice issue)
---

Add a checklist item to the current slice's description body.

User-supplied item text is in `$ARGUMENTS`. If empty, ask the user for the text before proceeding.

## Steps

1. Locate `.checklist.json` per the [Detection](${CLAUDE_PLUGIN_ROOT}/spec/detection.md) rules.
2. If none found, tell the user there's no checklist set up here and stop.
3. Extract `project` and `current_slice_issue`.
4. If `current_slice_issue` is `null`, tell the user no slice is set and stop.
5. Fetch the issue to verify state:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" get-issue <current_slice_issue>
   ```

6. If `state.type == "completed"` or state name is "Done", tell the user the slice is complete and stop.
7. Append the checkbox:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" append-checkbox <current_slice_issue> "<text>"
   ```

   Make sure the text is properly quoted to handle spaces and special characters.
8. Confirm to the user:

   ```
   Added to <issue-identifier> (<project>): "<text>"
   ```

If any wrapper command exits non-zero, surface the error message verbatim. Do not retry.

## Relevant spec docs

- [Detection](${CLAUDE_PLUGIN_ROOT}/spec/detection.md) — finding `.checklist.json`
- [The linear.py wrapper](${CLAUDE_PLUGIN_ROOT}/spec/the-linearpy-wrapper.md) — `get-issue` and `append-checkbox` reference
- [Slice body structure](${CLAUDE_PLUGIN_ROOT}/spec/slice-body-structure.md) — where `append-checkbox` inserts the item
- [Capture mode](${CLAUDE_PLUGIN_ROOT}/spec/capture-mode.md) — when to capture without asking vs. confirm first

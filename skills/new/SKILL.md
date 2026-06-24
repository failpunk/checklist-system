---
name: new
description: Add a checklist item to the current slice in Failpunk Linear (FAIL-### slice issues)
---

Add a checklist item to the current slice's description body.

User-supplied item text is in `$ARGUMENTS`. If empty, ask the user for the text before proceeding.

## Steps

1. Locate `.checklist.json` per the [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21) rules.
2. If none found, tell the user there's no checklist set up here and stop.
3. Extract `project` and `current_slice_issue`.
4. If `current_slice_issue` is `null`, tell the user no slice is set and stop.
5. Fetch the issue to verify state:

   ```
   python3 ~/.claude-adly/plugins/checklist/scripts/linear.py get-issue <current_slice_issue>
   ```

6. If `state.type == "completed"` or state name is "Done", tell the user the slice is complete and stop.
7. Append the checkbox:

   ```
   python3 ~/.claude-adly/plugins/checklist/scripts/linear.py append-checkbox <current_slice_issue> "<text>"
   ```

   Make sure the text is properly quoted to handle spaces and special characters.
8. Confirm to the user:

   ```
   Added to <issue-identifier> (<project>): "<text>"
   ```

If any wrapper command exits non-zero, surface the error message verbatim. Do not retry.

## Relevant spec docs

- [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21) — finding `.checklist.json`
- [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f) — `get-issue` and `append-checkbox` reference
- [Slice body structure](https://linear.app/failpunkllc/document/slice-body-structure-e645fed13bcc) — where `append-checkbox` inserts the item
- [Capture mode](https://linear.app/failpunkllc/document/capture-mode-6103e77ae078) — when to capture without asking vs. confirm first

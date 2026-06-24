---
name: status
description: Show open checklist items in the current slice (a FAIL-### issue in the personal Failpunk Linear workspace)
---

Show the user the open (unchecked) checklist items in the current slice. Project-scoped — does not show items from other projects.

## Steps

1. Locate `.checklist.json` per the [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21) rules.
2. If none found, tell the user there's no checklist set up here and stop.
3. Extract `project` and `current_slice_issue` from the file (see [The .checklist.json file](https://linear.app/failpunkllc/document/the-checklistjson-file-42b14155210c) for field semantics).
4. If `current_slice_issue` is `null`, tell the user no slice is set and stop.
5. Run via Bash:

   ```
   python3 ~/.claude-adly/plugins/checklist/scripts/linear.py get-issue <current_slice_issue>
   ```

6. Parse the JSON output. Extract `identifier`, `title`, and `description`.
7. From the `description` body, find every line that matches `- [ ] ...` (unchecked checkboxes only). Preserve their original order. Stop scanning at the first blank line followed by a `# ` heading — that's the boundary between checkbox block and plan content (see [Slice body structure](https://linear.app/failpunkllc/document/slice-body-structure-e645fed13bcc)).
8. **Count the items you found in step 7.** Call this N. Do not guess; the count must equal the number of items displayed.
9. Display, replacing N with the actual count:

   ```
   <project> · <title> (<identifier>) · N open

   - [ ] <full text of item 1, exactly as it appears in the body>
   - [ ] <full text of item 2>
   ...
   ```

   Always preserve the leading `- [ ] ` prefix on each item — these are checkboxes, not plain bullets. If items contain backticks or markdown formatting, leave them intact.
10. If N is 0, display:

    ```
    Nothing open in this slice. ✓
    ```

If the wrapper command exits non-zero, surface the error message verbatim.

## Relevant spec docs

- [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21) — finding `.checklist.json`
- [The .checklist.json file](https://linear.app/failpunkllc/document/the-checklistjson-file-42b14155210c) — schema and fields
- [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f) — `get-issue` subcommand reference
- [Slice body structure](https://linear.app/failpunkllc/document/slice-body-structure-e645fed13bcc) — checkbox block layout

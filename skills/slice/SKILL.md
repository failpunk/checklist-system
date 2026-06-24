---
name: slice
description: Manage the current slice (show, set, create, mark done + transition). Slices are FAIL-### issues in the personal Failpunk Linear workspace — use this skill's linear.py wrapper (NOT the Linear MCP) for any FAIL-### issue lookup or edit.
---

Manage the current slice for the project. All Linear interactions go through `~/.claude-adly/plugins/checklist/scripts/linear.py`.

The user's argument is in `$ARGUMENTS`. Branch on its shape:

- **empty** → show current slice info, then offer set / create / done / cancel.
- **`done`** (literal) → mark current slice Done, ask about carry-forward, create the next slice with an auto-generated title.
- **issue key like `FAIL-43` or bare number `43`** → set as the current slice (must be open and in the current project).
- **quoted title (anything else)** → create a new slice with that title and set as current.

## Common preamble (always run first)

1. Locate `.checklist.json` per the [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21) rules.
2. If none found, tell the user there's no checklist set up here and stop.
3. Extract `team`, `project`, `label`, `current_slice_issue`.

## Empty-arg branch (show + offer)

1. If `current_slice_issue` is null → tell the user there is no current slice; offer to create one and stop.
2. Fetch the issue:

   ```
   python3 ~/.claude-adly/plugins/checklist/scripts/linear.py get-issue <current_slice_issue>
   ```

3. Parse the JSON. Display:

   ```
   <project> · <title> (<identifier>) · <state name>
   <N> open items
   ```

   (Count `- [ ]` lines in the description body for N.)
4. Offer the user these options:
   - Set a different open slice as current (`/checklist:slice <key>`)
   - Create a new slice (`/checklist:slice "<title>"`)
   - Mark current done and transition (`/checklist:slice done`)
   - Cancel

   Stop after listing — don't act without an explicit follow-up command.

## Issue-key/number branch

1. Normalize: if `$ARGUMENTS` is a bare number, prefix with `FAIL-` (the team prefix). Otherwise use as-is.
2. Fetch the issue (see [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f) for `get-issue` reference).
3. Verify:
   - `project.name == <project from .checklist.json>` — if not, tell the user the issue belongs to a different project and stop.
   - `state.type != "completed"` — if it's Done, tell the user and offer to reopen in Linear UI first; stop.
4. Update `.checklist.json`: set `current_slice_issue` to the new key. Preserve all other fields.
5. Confirm: `Current slice set to <key>: "<title>".`

## `done` branch

1. If `current_slice_issue` is null → nothing to mark done; tell the user and stop.
2. Fetch the issue and save the result; you'll need the description body (for carry-forward) and title (for context).
3. Mark it done:

   ```
   python3 ~/.claude-adly/plugins/checklist/scripts/linear.py mark-done <current_slice_issue>
   ```

   The wrapper handles state lookup regardless of the team's exact "Done" state name (see [Slice state lifecycle](https://linear.app/failpunkllc/document/slice-state-lifecycle-c7e2df5dc679)).
4. From the saved description body, extract all `- [ ]` lines (open items only). Preserve original order and exact text after `- [ ] ` (see [Slice body structure](https://linear.app/failpunkllc/document/slice-body-structure-e645fed13bcc) for the layout).
5. If there are open items, ask: `Carry forward N open items to the new slice? (y/n, default y)`. Wait for an answer.
6. Generate a title for the new slice from recent context. Tell the user the chosen title and proceed.
7. Create the new slice:

   ```
   python3 ~/.claude-adly/plugins/checklist/scripts/linear.py create-issue <team> <project> "<auto-title>" <label>
   ```

   Capture the new identifier from the JSON output.
8. If carrying forward, for each open item:

   ```
   python3 ~/.claude-adly/plugins/checklist/scripts/linear.py append-checkbox <new-key> "<text>"
   ```

   (Items also remain in the closed slice — that's intentional history. Don't try to remove them.)
9. Update `.checklist.json`: set `current_slice_issue` to the new key.
10. Confirm:

    ```
    Closed <old-key> ("<old-title>"). Created <new-key>: "<auto-title>". Carried forward N items.
    ```

    (Adjust the trailing sentence if no carry-forward.)

## Quoted-title branch

1. Strip surrounding quotes from `$ARGUMENTS` if present. The remaining text is the title.
2. Create the new slice via `create-issue` (see [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f)).
3. Capture the new identifier. Update `.checklist.json`: set `current_slice_issue` to the new key.
4. Confirm: `Created <new-key>: "<title>". Set as current slice.`

## Error handling

If any wrapper command exits non-zero, surface the error message verbatim. Do not retry.
If `.checklist.json` is malformed, surface the error and stop. Do not attempt to repair.

## Relevant spec docs

- [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21) — finding `.checklist.json`
- [The .checklist.json file](https://linear.app/failpunkllc/document/the-checklistjson-file-42b14155210c) — field semantics
- [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f) — `get-issue`, `create-issue`, `mark-done`, `append-checkbox`
- [Slice body structure](https://linear.app/failpunkllc/document/slice-body-structure-e645fed13bcc) — extracting open items, preserving the checkbox block
- [Slice state lifecycle](https://linear.app/failpunkllc/document/slice-state-lifecycle-c7e2df5dc679) — Todo / In Progress / Done transitions
- [Hard rules](https://linear.app/failpunkllc/document/hard-rules-f2f5a01594d2) — confirm before destructive actions

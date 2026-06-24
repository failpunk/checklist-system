---
name: slice
description: Manage the current slice (show, set, create, mark done + transition). Slices are Linear issues — use this skill's linear.py wrapper (NOT the Linear MCP) for any slice issue lookup or edit.
---

Manage the current slice for the project. All Linear interactions go through `${CLAUDE_PLUGIN_ROOT}/scripts/linear.py`.

The user's argument is in `$ARGUMENTS`. Branch on its shape:

- **empty** → show current slice info, then offer set / create / done / cancel.
- **`done`** (literal) → mark current slice Done, ask about carry-forward, create the next slice with an auto-generated title.
- **issue key like `ABC-43` or bare number `43`** → set as the current slice (must be open and in the current project).
- **quoted title (anything else)** → create a new slice with that title and set as current.

## Common preamble (always run first)

1. Locate `.checklist.json` per the [Detection](${CLAUDE_PLUGIN_ROOT}/spec/detection.md) rules.
2. If none found, tell the user there's no checklist set up here and stop.
3. Extract `team`, `project`, `label`, `current_slice_issue`.

## Empty-arg branch (show + offer)

1. If `current_slice_issue` is null → tell the user there is no current slice; offer to create one and stop.
2. Fetch the issue:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" get-issue <current_slice_issue>
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

1. Normalize `$ARGUMENTS` into a full issue key:
   - If it already looks like a key (`<PREFIX>-<number>`), use it as-is.
   - If it's a bare number, prefix it with the team's issue-key prefix. Derive that prefix from `current_slice_issue` (the part before the `-`, e.g. `ABC` from `ABC-12`). If there is no current slice to derive the prefix from, ask the user for the full issue key instead of guessing.
2. Fetch the issue (see [The linear.py wrapper](${CLAUDE_PLUGIN_ROOT}/spec/the-linearpy-wrapper.md) for `get-issue` reference).
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
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" mark-done <current_slice_issue>
   ```

   The wrapper handles state lookup regardless of the team's exact "Done" state name (see [Slice state lifecycle](${CLAUDE_PLUGIN_ROOT}/spec/slice-state-lifecycle.md)).
4. From the saved description body, extract all `- [ ]` lines (open items only). Preserve original order and exact text after `- [ ] ` (see [Slice body structure](${CLAUDE_PLUGIN_ROOT}/spec/slice-body-structure.md) for the layout).
5. If there are open items, ask: `Carry forward N open items to the new slice? (y/n, default y)`. Wait for an answer.
6. Generate a title for the new slice from recent context. Tell the user the chosen title and proceed.
7. Create the new slice:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" create-issue <team> <project> "<auto-title>" <label>
   ```

   Capture the new identifier from the JSON output.
8. If carrying forward, for each open item:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" append-checkbox <new-key> "<text>"
   ```

   (Items also remain in the closed slice — that's intentional history. Don't try to remove them.)
9. **Post the wrap-up comment** (required) on the slice you just closed. Compose a concise, human-readable markdown summary and post it via stdin:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" create-comment <current_slice_issue> -
   ```

   Build the markdown from the saved body and what you just did, following this shape:

   ```
   ## Slice wrap-up

   **What landed:**
   - <each completed `- [X]` item from the saved body, in order>

   **Carried forward:** <N item(s) to <new-key>>, or "None".

   **Notes:** <decisions, follow-ups, or why any open items were dropped, if any>
   ```

   Keep it concrete; if there were no completed items, say so plainly instead of padding. This is required on every close (see [Slice state lifecycle](${CLAUDE_PLUGIN_ROOT}/spec/slice-state-lifecycle.md) and [Hard rules](${CLAUDE_PLUGIN_ROOT}/spec/hard-rules.md)).
10. Update `.checklist.json`: set `current_slice_issue` to the new key.
11. Confirm:

    ```
    Closed <old-key> ("<old-title>"). Created <new-key>: "<auto-title>". Carried forward N items.
    ```

    (Adjust the trailing sentence if no carry-forward.)

## Quoted-title branch

1. Strip surrounding quotes from `$ARGUMENTS` if present. The remaining text is the title.
2. Create the new slice via `create-issue` (see [The linear.py wrapper](${CLAUDE_PLUGIN_ROOT}/spec/the-linearpy-wrapper.md)).
3. Capture the new identifier. Update `.checklist.json`: set `current_slice_issue` to the new key.
4. Confirm: `Created <new-key>: "<title>". Set as current slice.`

## Error handling

If any wrapper command exits non-zero, surface the error message verbatim. Do not retry.
If `.checklist.json` is malformed, surface the error and stop. Do not attempt to repair.

## Relevant spec docs

- [Detection](${CLAUDE_PLUGIN_ROOT}/spec/detection.md) — finding `.checklist.json`
- [The .checklist.json file](${CLAUDE_PLUGIN_ROOT}/spec/the-checklistjson-file.md) — field semantics
- [The linear.py wrapper](${CLAUDE_PLUGIN_ROOT}/spec/the-linearpy-wrapper.md) — `get-issue`, `create-issue`, `mark-done`, `append-checkbox`
- [Slice body structure](${CLAUDE_PLUGIN_ROOT}/spec/slice-body-structure.md) — extracting open items, preserving the checkbox block
- [Slice state lifecycle](${CLAUDE_PLUGIN_ROOT}/spec/slice-state-lifecycle.md) — Todo / In Progress / Done transitions
- [Hard rules](${CLAUDE_PLUGIN_ROOT}/spec/hard-rules.md) — confirm before destructive actions

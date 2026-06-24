## Lifecycle

| State | Meaning |
| -- | -- |
| `Todo` | Newly created slice, or all items currently unchecked. |
| `In Progress` | At least one checkbox checked but not all. |
| `Done` | All checkboxes checked. |

## Auto-transition

`check-item` and `uncheck-item` **auto-transition** the slice's state to match the lifecycle on every write:

* All checked → `Done`
* Mixed → `In Progress`
* All unchecked → `Todo`

Transitions are skipped when the slice has no checkboxes, or when already in the target state. `get-issue` also nudges `Todo` → `In Progress` as a safety net when it sees checked items (helpful when the user checked something directly in the Linear UI).

If a project's norms diverge from this lifecycle, follow the project. Multiple `In Progress` slices in the same project are allowed (e.g. when sub-agents are working in parallel).

## Project status roll-up (promote-only)

Slice transitions also roll up to the parent project, in one direction only (full rules: [Project hygiene](./project-hygiene.md)):

* A slice entering `In Progress` promotes its project from Backlog/Planned to In Progress (skipped when already there, and for machine-hub projects).
* Nothing in the automation ever demotes a project or marks it Completed. Completing a project always requires the user's explicit OK.

`check-item`, `uncheck-item`, `set-state`, `mark-done`, and `sync-slice-state` all apply the roll-up.

## Manual overrides

* `linear.py set-state <key> <state-name>` — set state to a named state (case-insensitive). Idempotent.
* `linear.py mark-done <key>` — set state to a `completed`-type state. Works regardless of the team's exact "Done" state name.

## Closing a slice (wrap-up comment required)

Whenever a slice is closed (via `mark-done`, the `/checklist:slice done` flow, or a natural-language "close this slice" / "wrap this up"), post a wrap-up **comment** on that slice. This is required, not optional: it is the human-readable record of how the slice ended, so a person can understand the outcome later without reverse-engineering the checkboxes.

The comment, in clean Linear-rendered markdown, states:

* **What was done** — the completed items, i.e. what actually landed.
* **Any other updates** — items carried forward (and to which new slice), decisions made, follow-ups, or why open items were dropped.

Post it with `linear.py create-comment <key> -` (markdown on stdin). Keep it concise and concrete.

## See also

* [Slice body structure](./slice-body-structure.md)
* [The linear.py wrapper](./the-linearpy-wrapper.md)

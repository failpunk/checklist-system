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

Slice transitions also roll up to the parent project, in one direction only (full rules: [Project hygiene](https://linear.app/failpunkllc/document/project-hygiene-26c390f7c1ab)):

* A slice entering `In Progress` promotes its project from Backlog/Planned to In Progress (skipped when already there, and for machine-hub projects).
* Nothing in the automation ever demotes a project or marks it Completed. Completing a project always requires the user's explicit OK.

`check-item`, `uncheck-item`, `set-state`, `mark-done`, and `sync-slice-state` all apply the roll-up.

## Manual overrides

* `linear.py set-state <key> <state-name>` — set state to a named state (case-insensitive). Idempotent.
* `linear.py mark-done <key>` — set state to a `completed`-type state. Works regardless of the team's exact "Done" state name.

## See also

* [Slice body structure](https://linear.app/failpunkllc/document/slice-body-structure-e645fed13bcc)
* [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f)

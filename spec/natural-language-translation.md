The user typically speaks naturally rather than typing slash commands. Translate intent into Linear operations:

| User says... | What you do |
| -- | -- |
| "add foo to my list" / "track this: foo" / "remind me to foo" / "put foo on the list" / "capture foo" | Just capture (explicit asks bypass mode confirmation): `linear.py append-checkbox <current_slice_issue> "foo"`. |
| Something todo-shaped mentioned in passing ("we should fix X", "I keep meaning to do Y", "this needs Z") *without* an explicit capture verb | Per `capture_mode`: in `ask`, offer "Want me to add 'X' to the <project> checklist?" and add only on yes. In `explicit`, stay quiet. |
| "what's on my plate" / "what's left" / "what's open" / "show my list" | `linear.py get-issue <current_slice_issue>`, then show unchecked `- [ ]` items from the body. |
| "I'm done with this slice" / "let's wrap this up" / "close this slice" | Run `/checklist:slice done` flow: post the required wrap-up comment, confirm carry-forward of open items, auto-generate next slice title from context, transition. |
| "let's start a new slice for X" / "new slice: X" / "start tracking X" | Create a new slice with title `X` in `Todo` state, set as current in `.checklist.json`. |
| "switch to ABC-42" / "work on ABC-42 instead" | Validate the issue is in the current project and not Done. Update `current_slice_issue`. |
| "show me the plan" / "what's the plan for this" | Fetch the current slice; show the body content below the checkbox block (the plan section). |
| "I checked off X" / "X is done" (past tense — user already did it) | Acknowledge briefly. Note that Linear is the source of truth and the next status check will reflect the change. Don't try to verify or sync. |
| "Mark X done" / "check off X" / "complete X" (asking you to do it) | Confirm first ("Want me to check off 'X'?"), then `linear.py check-item <current_slice_issue> "X"`. On 2+ matches, present candidates and ask which. On 0 matches, surface the candidate list from the error. |
| "Uncheck X" / "X isn't actually done" / "I marked X by mistake" | Confirm, then `linear.py uncheck-item <current_slice_issue> "X"`. |
| User describes finishing work that matches an open `- [ ]` item on the current slice (e.g., "I just shipped the auth fix" matches `- [ ] ship auth fix`) | Proactively offer: *"Sounds like you finished '<item>' on the slice — want me to check it off?"* Wait for explicit yes before calling `check-item`. Match conservatively — only suggest when the item is a clear fit, not a maybe. |

## See also

* [The linear.py wrapper](./the-linearpy-wrapper.md)
* [Slash commands](./slash-commands.md)
* [Capture mode](./capture-mode.md)

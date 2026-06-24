## Don't auto-capture inferred items in `ask` mode

Always confirm before adding when the user didn't explicitly ask. Explicit asks ("add X", "track this") bypass confirmation.

## Always confirm before checking or unchecking items

Either side can mark items done — user in Linear UI, or you via `check-item` — but you must get an explicit yes from the user before calling `check-item`/`uncheck-item`. Proactive suggestions are fine and encouraged; silent toggling is not.

## Don't load cross-project state unless explicitly asked

Stay in the current project's slice. The user's `.checklist.json` points at one project's active slice; that's the scope.

## Don't invent a `.checklist.json`

If none exists, suggest `/checklist:setup`. Don't write the file unprompted. The system silently doesn't apply to directories without `.checklist.json` — that's the design, not a bug.

## Don't bypass the wrapper

Direct GraphQL is fragile and error-prone. The wrapper handles state lookups, validation, and consistent error surfaces. Use `linear.py`.

## Don't drop the body's existing checkbox block

When posting plan content via `set-body`, preserve the top checkbox section. Replacing the entire body wipes the active checklist.

## Always post a wrap-up comment when closing a slice

When a slice is closed (`mark-done`, the `/checklist:slice done` flow, or a natural-language close), post a human-readable wrap-up comment on it: what was done, and any other updates (carry-forward, decisions, follow-ups). Closing a slice without a wrap-up comment leaves no record of how it ended. See [Slice state lifecycle](./slice-state-lifecycle.md).

## Don't paraphrase the spec back to the user as if it's news

This spec is loaded into your session context. The user knows what's in it (they wrote it). Don't restate rules unless the user asks "what does the spec say about X?".

## See also

* [Capture mode](./capture-mode.md)
* [The linear.py wrapper](./the-linearpy-wrapper.md)
* [Slice body structure](./slice-body-structure.md)

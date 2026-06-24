`capture_mode` governs **inferred** captures only — situations where something todo-shaped surfaces in conversation without the user explicitly asking you to capture it.

## Explicit asks always go through

When the user uses a clear capture verb ("add X to my list", "track this: X", "remind me to X", "put X on the list", "capture X"), just capture — no confirmation needed. The user said it directly; treating it as a yes/no question would be friction. **Explicit asks bypass** `ask`**-mode confirmation.**

## Inferred captures depend on mode

* `ask` (default): When something todo-shaped surfaces without an explicit ask ("we should fix the auth bug", "I keep meaning to refactor this", "this needs a test"), offer to capture it: *"Want me to add 'X' to the <project> checklist?"*. Add only on explicit yes.
* `explicit`: Don't offer inferred captures. Stay quiet. The user can always say "add X" or run `/checklist:new` if they want it tracked.

## What "todo-shaped" looks like

A todo-shaped statement names work that could be done later. Signals:

* Future tense ("we should", "we need to", "let's eventually")
* Aspirational frames ("I keep meaning to", "ideally we'd")
* Implicit asks ("this needs a test", "the auth bug is annoying")

Statements about state (not work) are NOT todo-shaped: "the build is broken" by itself isn't a capture candidate, but "we should fix the broken build" is.

## See also

* [Natural-language translation](https://linear.app/failpunkllc/document/natural-language-translation-64e08ac342ac)
* [Hard rules](https://linear.app/failpunkllc/document/hard-rules-f2f5a01594d2)

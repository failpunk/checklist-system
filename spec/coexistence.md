The checklist system coexists with other persistence mechanisms. Use the right tool for the right scope.

## TodoWrite (session-scoped)

Claude Code's `TodoWrite` tool tracks current-session work that doesn't outlive the session. Linear checklist items are cross-session, high-level. Both coexist without conflict — use TodoWrite for in-session step tracking, use the Linear slice for things you want to find next week.

## superpowers:writing-plans / superpowers:executing-plans

Local plan files at `docs/superpowers/plans/*.md` continue to be the source for the executing-plans flow.

**Mirror policy (set 2026-06-12):** whenever a plan or spec file is written or substantively updated for slice-tracked work, mirror its content to the Linear slice's body via `linear.py set-body` (preserving the top checkbox section) **at write time — in the same session, before the task ends**. Do not defer the mirror to a wrap-up step; sessions that exit mid-stream are how slices silently fall out of date. A PostToolUse hook in the checklist plugin (`hooks/post-tool-use/mirror-plan-spec.sh`) injects a reminder whenever `docs/superpowers/{plans,specs}/*.md` is written inside a checklist-governed directory; trivial edits (typos, formatting) are exempt.

Local plan files and Linear slices may still drift as items get checked off in different places — that's expected. Linear is the user-facing async tracker; the local file is the executing-plans source.

## Directories without `.checklist.json`

The checklist system silently doesn't apply. Don't suggest onboarding mid-task — only when the user explicitly asks. Existing project conventions (`TODO.md`, scattered notes, items in other Linear orgs) keep working as before.

## See also

* [Detection](./detection.md)
* [Overview](./overview.md)
* [Slice body structure](./slice-body-structure.md)

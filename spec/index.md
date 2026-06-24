<!-- BUNDLED SPEC: static copy of the Checklist System spec, shipped with the plugin so it
works without access to any private Linear workspace. Editing source is the maintainer's
Linear docs; regenerate this bundle on release. -->

**You are an agent reading this team document because a** `.checklist.json` **file was detected in the current working directory. This document is the canonical spec for the checklist system you'll be helping the user with.**

A personal cross-project checklist tracker backed by Linear. When `.checklist.json` exists in a directory (or any parent up to `$HOME`), that directory is onboarded into the system, and high-level todos for the project live in a Linear *slice issue* — not in `TODO.md`, plan files, or scattered notes.

## How to use this spec

This page is the entry point. It tells you what the system is and points at the other documents that hold the details. **The other 13 documents are linked below; fetch a specific one when you need its details.** You do not need to fetch all of them upfront — the SessionStart hook loaded just this overview into your context to keep session-start small.

To read a specific document, open the matching file in this `spec/` directory (e.g. `spec/overview.md`).



## Spec documents (in reading order)

 1. [Overview](./overview.md) — What the system is, two audiences (user vs agent), and the three-artifact architecture.
 2. [Detection](./detection.md) — How to find `.checklist.json`. When the system applies vs silently doesn't.
 3. [The .checklist.json file](./the-checklistjson-file.md) — Schema and field semantics. Read this when you need to interpret a project's config.
 4. [Capture mode](./capture-mode.md) — `ask` vs `explicit`, and the rule that explicit asks always bypass confirmation.
 5. [Natural-language translation](./natural-language-translation.md) — The big table mapping common user phrases to Linear operations. Read this when figuring out what the user means.
 6. [Slice body structure](./slice-body-structure.md) — Checkbox + plan layout. Read before posting plan content via `set-body`.
 7. [Slice state lifecycle](./slice-state-lifecycle.md) — Todo/In Progress/Done, auto-transition rules, manual overrides.
 8. [Cross-entity references](./cross-entity-references.md) — How to link to other Linear entities (issues, projects, initiatives, documents) using canonical URLs.
 9. [The linear.py wrapper](./the-linearpy-wrapper.md) — Full subcommand reference for the Python wrapper. Read this when constructing a Linear operation.
10. [Slash commands](./slash-commands.md) — The escape-hatch `/checklist:*` commands and where their files live.
11. [Hard rules](./hard-rules.md) — The don'ts. Read all of them.
12. [Coexistence](./coexistence.md) — How the checklist system relates to TodoWrite, plan files, and non-onboarded directories.
13. [Project hygiene](./project-hygiene.md) — The bar every project must meet (description, spec/plan resources, accurate status), promote-only status sync, milestone health updates, machine hubs.

## When to fetch what

* **User asks "what's on my plate"** → no spec lookup needed; just run `linear.py get-issue <current_slice_issue>`.
* **User says something todo-shaped** → fetch [Capture mode](./capture-mode.md) if you're unsure whether to capture.
* **User wants to do a Linear operation** → fetch [The linear.py wrapper](./the-linearpy-wrapper.md) for the exact subcommand.
* **You're posting plan content to a slice** → fetch [Slice body structure](./slice-body-structure.md) to make sure you don't wipe the checkboxes.
* **You're about to check or uncheck an item** → fetch [Hard rules](./hard-rules.md) — there's a confirmation rule that's easy to skip.
* **You're creating a project or touching a project's status, description, or resources** → fetch [Project hygiene](./project-hygiene.md) for the bar and the promote-only sync rules.
* **First time touching the system in a session** → fetch [Overview](./overview.md) for the two-audience framing.

## Architecture

Three artifacts, three distribution mechanisms:

| Artifact | What it is | Single source | Distribution |
| -- | -- | -- | -- |
| **Spec** | These documents | Bundled with the plugin (`spec/`) | SessionStart hook loads this page per session |
| **Tooling** | `linear.py`, hook script, slash command files | The `checklist` Claude Code plugin | Plugin install + user-level command files |
| **Per-user config** | `LINEAR_API_KEY` env var | User shell config | Documented in plugin README |

Scope: Claude Code only for v1. Non-CC agents (Cursor, Cline, etc) are a future concern.

## Editing the spec

The spec ships bundled with the plugin in the `spec/` directory. To change it, edit those files and reinstall the plugin; the next session start picks up the new content.

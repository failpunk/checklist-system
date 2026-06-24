All Linear interactions go through `linear.py`. Use this, not direct GraphQL — the wrapper handles state lookups, validation, and consistent error surfaces.

## Location

`linear.py` lives in the `checklist` Claude Code plugin at `~/.claude-adly/plugins/checklist/scripts/linear.py`.

## Issue / slice subcommands

| Subcommand | Purpose |
| -- | -- |
| `get-issue <key>` | Fetch issue (id, title, url, body, state, project, labels). |
| `append-checkbox <key> <text>` | Add a checkbox at the top of the body's checkbox block. |
| `check-item <key> <text>` | Flip `- [ ] text` → `- [x] text` and auto-transition slice state. Errors with candidate list on 0 or 2+ matches. |
| `uncheck-item <key> <text>` | Flip `- [x] text` → `- [ ] text` and auto-transition slice state. Same matching rules. |
| `create-issue <team> <project> <title> <label>` | New slice in `Todo` state with the project + label applied. |
| `mark-done <key>` | Set state to a `completed`-type state. |
| `set-state <key> <state-name>` | Set state to a named state (case-insensitive). Idempotent. |
| `set-body <key> <markdown \| -for-stdin>` | Overwrite the issue body. Use `-` to read from stdin. |

## Team / project / label subcommands

| Subcommand | Purpose |
| -- | -- |
| `list-projects <team>` | Projects in the team. |
| `list-labels <team>` | Labels in the team. |
| `list-open-slices <team> <project>` | Open slices in a project. |
| `audit-projects <team>` | Read-only project-hygiene audit of a whole team: per-project status, description length, resource presence, open slices, and flags (`needs_promotion`, `missing_description`, `missing_resources`, `status_possibly_stale`). Only `needs_promotion` should trigger a write (promote-only). |
| `create-project <team> <name> <description \| -for-stdin> [--color <hex>]` | Create a Linear project. Description is required ([Project hygiene](./project-hygiene.md)): what it is, where it lives on disk, how to pick it up cold. Defaults to blue `#26b5ce`. |
| `update-project <team> <name> [--description <text \| ->] [--content <markdown \| ->] [--status <name>]` | Update a project's short description (list view, 255-char cap), overview body, and/or status. At least one flag. |
| `add-project-resource <team> <name> <url> <label...>` | Add a link to the project's Resources section (spec, plan, Living Docs). |
| `post-project-update <team> <name> <body \| -for-stdin> [--health onTrack\|atRisk\|offTrack]` | Post a project update (the Health column). Defaults to onTrack. Post on milestones: slice done, project state change. |
| `create-label <team> <name>` | Create a Linear label. Auto-picks the least-used team palette color. |

## Initiative subcommands

| Subcommand | Purpose |
| -- | -- |
| `get-initiative <name>` | Fetch initiative metadata (id, url, description, content length). |
| `get-initiative-content <name>` | Fetch the initiative `content` field (markdown body) to stdout. |
| `create-initiative <name> [--color <hex>] [--description <text>]` | Create an initiative. Defaults to red `#eb5757`. |
| `add-project-to-initiative <initiative> <project>` | Link a project to an initiative. Idempotent. |

## Document subcommands

| Subcommand | Purpose |
| -- | -- |
| `list-initiative-documents <initiative>` | List documents attached to an initiative. |
| `get-document <doc-id>` | Fetch document metadata + content. |
| `get-document-content <doc-id>` | Fetch just the content (markdown body) to stdout. |
| `create-document <initiative> <title> <markdown \| -for-stdin> [--color <hex>]` | Create a document attached to the initiative. Defaults to orange `#f2994a`. |
| `update-document <doc-id> <markdown \| -for-stdin> [--color <hex>]` | Overwrite document content. `--color` is optional; color is left unchanged if omitted. |

## Creating object types (and their colors)

Every Linear object type has a standard color in this workspace (see [Cross-entity references](./cross-entity-references.md) for the full scheme). When you create an object, attach its color:

| Object type | How to create | Color | Hex |
| -- | -- | -- | -- |
| **Initiative** | `create-initiative <name>` — color applied automatically. Override with `--color <hex>`. | red | `#eb5757` |
| **Project** | `create-project <team> <name> <description>` — color applied automatically. Override with `--color <hex>`. | blue | `#26b5ce` |
| **Document** | `create-document <initiative> <title> <body>` — color applied automatically. Override with `--color <hex>`. | orange | `#f2994a` |
| **Issue / slice** | `create-issue <team> <project> <title> <label>` — no per-issue color; issues take their color from the applied label. | (via label) | — |

The color defaults live in `linear.py` as `DEFAULT_INITIATIVE_COLOR`, `DEFAULT_PROJECT_COLOR`, and `DEFAULT_DOC_COLOR`.

## API key

The wrapper reads the API key from `$LINEAR_API_KEY`, the macOS Keychain (service `linear-checklist`), or `~/.config/checklist/api-key` (mode 600), in that order. All errors exit non-zero with a clear message; surface them verbatim if the user needs to see them.

## See also

* [Cross-entity references](./cross-entity-references.md)
* [Natural-language translation](./natural-language-translation.md)
* [Project hygiene](./project-hygiene.md)

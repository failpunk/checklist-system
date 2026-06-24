When body content references another Linear entity (issue, project, initiative, or document), use the canonical URL. Linear renders these URLs as rich cards with title and state; bare identifiers stay as inline code.

## Canonical URL patterns

* **Issue**: `https://linear.app/failpunkllc/issue/<key>/<slug>` — get from `linear.py get-issue <key>` (the `url` field).
* **Project**: `https://linear.app/failpunkllc/project/<slug>-<id>` — get from the Linear UI or via the project's URL field.
* **Initiative**: `https://linear.app/failpunkllc/initiative/<slug>-<id>` — get from `linear.py get-initiative <name>`.
* **Document**: `https://linear.app/failpunkllc/document/<slug>-<id>` — get from `linear.py get-document <id>` or `list-initiative-documents <initiative>`.

## Live examples

Here are examples of each entity type as a native Linear link. In the Linear UI these render as rich cards with title, state, and an icon. In the markdown body they're stored as plain URLs.

* **Initiative**: [Checklist System](https://linear.app/failpunkllc/initiative/checklist-system-619094c78b45)
* **Project**: [Clip Cabinet](https://linear.app/failpunkllc/project/clip-cabinet-a1f7bbef52c8)
* **Issue**: [FAIL-33](https://linear.app/failpunkllc/issue/FAIL-33/checklist-system-package-as-portable-claude-code-plugin-linear-initiative-spec)
* **Document** (another doc in this initiative): [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f)

Each rendered as a card. The markdown stored is just the bare URL on its own line; Linear's renderer does the rest.

## Color scheme

Linear entities follow a fixed color scheme by type, so the entity type is recognizable at a glance. When creating any entity, set its color to match:

| Entity | Color | Hex |
| -- | -- | -- |
| Initiative | red | `#eb5757` |
| Project | blue | `#26b5ce` |
| Document | orange | `#f2994a` |

`linear.py` applies these colors automatically on create — `create-initiative` → red, `create-project` → blue, `create-document` → orange (each overridable with `--color <hex>`); `update-document` accepts an optional `--color`. Issues take their color from the applied label.

## Inside the Linear web editor

You can also use the `@`-mention syntax inside Linear's web editor to autocomplete any entity. The underlying markdown stored is still the canonical URL form, so agents using the API see URLs either way.

## Markdown gotcha

Linear auto-converts strings like `CLAUDE.md` (anything ending in `.md`) into `[CLAUDE.md](<http://CLAUDE.md>)` because its renderer treats `.md` as a TLD. To avoid this in body content, write `CLAUDE-md` or use the full path (`~/.claude/CLAUDE.md`).

## See also

* [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f)
* [Overview](https://linear.app/failpunkllc/document/overview-93132484f842)

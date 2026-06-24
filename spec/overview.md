A personal cross-project checklist tracker backed by Linear. When `.checklist.json` exists in a directory (or any parent up to `$HOME`), that directory is onboarded into the system, and high-level todos for the project live in a Linear *slice issue* — not in `TODO.md`, plan files, or scattered notes.

## Three artifacts

| Artifact | What it is | Single source | Distribution |
| -- | -- | -- | -- |
| **Spec** | These documents | Bundled with the plugin (`spec/`) | SessionStart hook loads per session |
| **Tooling** | `linear.py`, hook script, slash command files | The `checklist` Claude Code plugin | Plugin install + user-level command files |
| **Per-user config** | `LINEAR_API_KEY` env var | User shell config | Documented in plugin README |

The spec ships bundled with the plugin in the `spec/` directory. Each document below covers one concept; they cross-reference each other as relative files in that directory.

## Two audiences

1. **The user** views and manages todos through Linear's web and mobile apps. Reads, scans, checks off items there. Rarely types slash commands.
2. **You (the agent)** do the bulk of the work programmatically — capturing items as they arise in conversation, managing slices, suggesting state transitions, running the wrapper. You translate the user's natural-language intent into Linear operations.

Slash commands (`/checklist:*`) are escape hatches for explicit user control; don't expect them to be typed often. The user mostly speaks naturally; you translate.

## See also

* [Detection](./detection.md)
* [The .checklist.json file](./the-checklistjson-file.md)

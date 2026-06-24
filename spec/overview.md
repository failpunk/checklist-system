A personal cross-project checklist tracker backed by Linear. When `.checklist.json` exists in a directory (or any parent up to `$HOME`), that directory is onboarded into the system, and high-level todos for the project live in a Linear *slice issue* — not in `TODO.md`, plan files, or scattered notes.

## Three artifacts

| Artifact | What it is | Single source | Distribution |
| -- | -- | -- | -- |
| **Spec** | The documents in this initiative | Linear initiative `Checklist System` | SessionStart hook fetches per session |
| **Tooling** | `linear.py`, hook script, slash command files | The `checklist` Claude Code plugin | Plugin install + user-level command files |
| **Per-user config** | `LINEAR_FAILPUNK_API_KEY` env var | User shell config (`~/.zshrc`) | Documented in plugin README |

The spec lives at the [Checklist System initiative](<https://linear.app/failpunkllc/initiative/checklist-system-619094c78b45>). Each document below covers one concept; documents cross-reference each other using their canonical Linear URLs.

## Two audiences

1. **The user** views and manages todos through Linear's web and mobile apps. Reads, scans, checks off items there. Rarely types slash commands.
2. **You (the agent)** do the bulk of the work programmatically — capturing items as they arise in conversation, managing slices, suggesting state transitions, running the wrapper. You translate the user's natural-language intent into Linear operations.

Slash commands (`/checklist:*`) are escape hatches for explicit user control; don't expect them to be typed often. The user mostly speaks naturally; you translate.

## See also

* [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21)
* [The .checklist.json file](https://linear.app/failpunkllc/document/the-checklistjson-file-42b14155210c)

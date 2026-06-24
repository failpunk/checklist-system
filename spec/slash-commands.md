Slash commands are escape hatches for explicit user control. The user can type them, or you can invoke their flows directly when natural language maps to them.

| Command | What it does |
| -- | -- |
| `/checklist:new "..."` | Append a checkbox to the current slice. |
| `/checklist:status` | Show open items in the current slice. |
| `/checklist:slice [arg]` | Manage the current slice (show / set / create / done). |
| `/checklist:setup` | Onboard the current directory into the system, including migrating items from existing `TODO.md` / plan files. |

## Where the command files live

User-level files at `~/.claude/commands/checklist/*.md`. Each file is the prompt-instructions an agent follows when the command is invoked. These mirror the source-of-truth versions in the plugin's `skills/<name>/SKILL.md`; until Claude Code's native plugin slash-command discovery is figured out for non-marketplace local plugins, the user-level command files are what actually resolves `/checklist:*` invocations.

## Most checklist work uses natural language

The user mostly speaks naturally; you translate. Slash commands exist for the rare case the user wants to invoke a precise flow without negotiation. Don't expect them to be typed often.

## See also

* [Natural-language translation](./natural-language-translation.md)
* [Capture mode](./capture-mode.md)

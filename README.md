# Linear Checklist System (Claude Code plugin)

A personal, cross-project todo tracker for Claude Code, backed by **Linear**. Each onboarded
project keeps its high-level todos in a Linear **"slice" issue**;
Claude loads that slice (and the system's spec) into context at the start of every session, so
your agent always knows what's on your plate and updates it as work completes.

## Install

**Prerequisites:** Claude Code · **Python 3** on your PATH (runs `linear.py` + the hooks) · a
**Linear** account + a **personal API key** with read + write (<https://linear.app/settings/api>) ·
**macOS or Linux** (hooks are bash + Python; on Windows use WSL or Git Bash).

**1. Add the marketplace and install the plugin** in Claude Code:

```
/plugin marketplace add https://github.com/failpunk/checklist-system
/plugin install checklist@checklist-system
```

Use the full HTTPS URL (not the `owner/repo` shorthand) so the marketplace clones over HTTPS
(no GitHub SSH key required). Installing registers the slash commands and the SessionStart hook
automatically (via the plugin's `hooks.json`) — no manual settings.json editing.

**2. Set your Linear API key** one of three ways (checked in this order):

1. Env var: `export LINEAR_API_KEY="lin_api_..."`
2. macOS Keychain (macOS only): `security add-generic-password -U -s linear-checklist -a "$USER" -w`
3. File: `~/.config/checklist/api-key` (chmod 600)

**3. Onboard a project.** In your Linear workspace, create a **Team** and a **Project** (and
optionally a label). Then, in any repo:

```
/checklist:setup
```

This writes a `.checklist.json` (team / project / label / capture_mode) and creates your first
slice. From then on, every Claude session in that directory loads the slice and the spec.

## Why we built it

Before AI, work was tracked as many small, human-sized issues. When you're orchestrating changes
instead of hand-writing code, that swarm of tickets becomes more bookkeeping than building.

Inspired by Claude's "superpowers" slices, this packs a whole unit of work — checklist *and* plan
— into **one Linear issue**: fewer, bigger, self-contained slices instead of micro-tickets. Each
slice is also the agent's memory — it loads into context automatically every session, so the agent
always knows the plan without re-briefing.

## What you get

Everything ships **bundled** in the plugin — the spec, the slash-command skills, a SessionStart
hook that auto-loads your current slice each session, the `linear.py` API wrapper, and an
optional status-bar widget.

- A `.checklist.json` in any repo marks it as tracked. A SessionStart hook detects it and injects
  the current slice + the spec into context.
- Slash commands to manage slices: `/checklist:setup`, `/checklist:slice`, `/checklist:status`,
  `/checklist:new`.
- A Python wrapper (`scripts/linear.py`) the agent uses for all Linear operations.

## How it works

- **SessionStart hook** (`hooks/session-start/checklist-context.sh`): walks up from the cwd for a
  `.checklist.json`; if found, prints its contents + the bundled spec into context. Silent if none.
- **Spec** (`spec/`): the canonical rules, as static markdown (`spec/index.md` links the rest).
- **`scripts/linear.py`**: the Linear API wrapper (`get-issue`, `check-item`, `set-body`,
  `create-issue`, `archive-issue`, …). Run `python3 scripts/linear.py` with no args for the full
  subcommand list.

## Commands

| Command | What it does |
| --- | --- |
| `/checklist:setup` | Onboard the current directory (writes `.checklist.json`). |
| `/checklist:slice` | Show / set / create the current slice; mark done. |
| `/checklist:status` | Show open items in the current slice. |
| `/checklist:new` | Add a checklist item to the current slice. |

## Status bar widget (optional)

A small status-line widget shows your current slice's progress — e.g.
`ABC-123 ▰▰▰▱▱▱▱ 3/7` — read from the local `.checklist.state.json` cache (no
network). It falls back to the folder name when no slice is active.

To enable it:

1. Copy the bundled script somewhere stable and make it executable:
   ```
   cp statusline/checklist-statusline.sh ~/.checklist-statusline.sh
   chmod +x ~/.checklist-statusline.sh
   ```
2. Point `statusLine` at it in your Claude Code `settings.json` (your config dir):
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "sh \"$HOME/.checklist-statusline.sh\""
     }
   }
   ```

Requires `jq`. **If you already use a status line**, Claude Code allows only one —
copy the slice-rendering block out of `statusline/checklist-statusline.sh` into your
existing script instead of replacing it.

## Notes

- **Free Linear plan**: archived issues don't count toward the active-issue cap — use
  `linear.py archive-issue <KEY>` to clear completed work.
- This is an early share for feedback. Issues/PRs welcome.

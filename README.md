# Checklist System (Claude Code plugin)

A personal, cross-project todo tracker for Claude Code, backed by **Linear**. Each onboarded
project keeps its high-level todos in a Linear **"slice" issue**; Claude loads that slice (and the
system's spec) into context at the start of every session, so your agent always knows what's on
your plate and updates it as work completes.

The spec ships **bundled** with the plugin (`spec/`), so it works against *your own* Linear
workspace — no access to anyone else's workspace required.

> **Why does this exist?** When you're orchestrating AI changes instead of hand-writing code, a
> swarm of small Linear tickets becomes unmanageable. So each project's work lives as larger,
> self-contained **slices** — one Linear issue holds the whole checklist + plan — and loads into
> every session automatically, so the agent always knows the plan. Full rationale:
> **[PHILOSOPHY.md](./PHILOSOPHY.md)**.

## What you get

- A `.checklist.json` in any repo marks it as tracked. A SessionStart hook detects it and injects
  the current slice + the spec into context.
- Slash commands to manage slices: `/checklist:setup`, `/checklist:slice`, `/checklist:status`,
  `/checklist:new`.
- A Python wrapper (`scripts/linear.py`) the agent uses for all Linear operations.

## Prerequisites

- **Claude Code.**
- A **Linear** account + workspace (the free plan is fine; the tooling includes an `archive-issue`
  command for the 250-active-issue cap).
- A Linear **personal API key**: <https://linear.app/settings/api> (needs read + write).

## Install

```
/plugin marketplace add failpunk/checklist-system
/plugin install checklist
```

Installing registers the slash commands and the SessionStart hook automatically (via the plugin's
`hooks.json`) — no manual settings.json editing.

## Set up your API key

Provide your Linear key one of three ways (checked in this order):

1. Env var: `export LINEAR_API_KEY="lin_api_..."`
2. macOS Keychain: `security add-generic-password -U -s linear-checklist -a "$USER" -w`
3. File: `~/.config/checklist/api-key` (chmod 600)

## Onboard a project

In your Linear workspace, create a **Team** and a **Project** (and optionally a label). Then, in
any repo:

```
/checklist:setup
```

This writes a `.checklist.json` (team / project / label / capture_mode) and creates your first
slice. From then on, every Claude session in that directory loads the slice and the spec.

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
`FAIL-123 ▰▰▰▱▱▱▱ 3/7` — read from the local `.checklist.state.json` cache (no
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

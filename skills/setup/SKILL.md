---
name: setup
description: Bootstrap the checklist system (Linear-backed) in the current directory, including migration of existing todos
---

Onboard the user's current directory into the checklist tracking system. This drives a multi-step conversational flow with the user — pause at each question and wait for their answer; don't bulk-execute.

The Linear **team** is provided by the user during setup (step 1) and stored in `.checklist.json`. It is not hardcoded.

All Linear interactions go through `${CLAUDE_PLUGIN_ROOT}/scripts/linear.py`.

## 1. Pre-flight check + team

First, validate the Linear API key via Bash:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" whoami
```

If the wrapper errors with "no Linear API key found", stop and tell the user:

> The Linear API key isn't set up. Once it is, re-run `/checklist:setup`.
>
> - Create a personal API key (needs read + write): Linear → Settings → API → Personal API keys, or <https://linear.app/settings/api>
> - Then provide it one of three ways (checked in this order):
>   - Env var: add `export LINEAR_API_KEY="lin_api_..."` to your shell profile and reload it
>   - macOS Keychain: `security add-generic-password -U -s linear-checklist -a "$USER" -w`
>   - File: save to `~/.config/checklist/api-key` (then `chmod 600`)

If `whoami` succeeds, ask the user which Linear team should track this project's slices:

> *Which Linear team should track this project's slices? (the team name as it appears in Linear)*

When they answer, validate the team and fetch its project list via Bash:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" list-projects "<team>"
```

If that errors (e.g. unknown team), surface the message and re-ask for the team. On success, capture the team name — you'll write it to `.checklist.json` in step 9 — and hold the project list for step 4.

## 2. Detect existing config

Walk up from CWD looking for `.checklist.json` per the [Detection](${CLAUDE_PLUGIN_ROOT}/spec/detection.md) rules.

- **None found** → continue to step 3.
- **Found at CWD itself** → say briefly: "There's already a `.checklist.json` here pointing at `<project>` / `<slice-key>`." Then ask the obvious binary question: *"Overwrite or keep the existing one? (default: keep)"*. Stop unless they choose overwrite.
- **Found at a parent dir** → say briefly: "This directory is already covered by `<parent path>/.checklist.json` (project: `<project>`, slice: `<slice-key>`)." Then ask the obvious binary question: *"Continue tracking with the parent config, or create a new config for this project? (default: parent)"*. If parent → confirm and stop ("Sticking with the parent. Run `/checklist:status` to see what's open."). If new → continue to step 3.

## 3. Track config in git repo? (asked upfront, applied immediately)

Check via Bash if CWD is in a git repo:

```
git rev-parse --is-inside-work-tree 2>/dev/null
```

If **not** a git repo, skip this step.

If it **is** a git repo, ask:

> *Track the checklist config in your repo or ignore it with `.gitignore`? (y/n, default y)*

Map: **y** (or default) → track in the repo, do nothing to `.gitignore`. **n** → append `.checklist.json` to the local repo's `.gitignore` (creating the file if it doesn't exist), under a section like `# Personal checklist tracker`. Apply this now, before any other setup steps, so there's no window where the file exists outside `.gitignore` if the user chose to ignore it.

## 4. Project selection

Show the user the project list from step 1 (one per line). Ask:

> *Does this belong to an existing Linear project? (Or provide a new project name for Linear.)*

When they answer, check whether their response matches an existing project name (case-insensitive). If it matches, use it. If it doesn't match any existing project, briefly confirm: *"Create new project '<X>'? (y/n, default y)"*. On yes, draft a description per the [Project hygiene](${CLAUDE_PLUGIN_ROOT}/spec/project-hygiene.md) bar (what this is, where it lives on disk, how to pick it up cold), confirm the wording with the user, then run via Bash:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" create-project "<team>" "<name>" "<description>"
```

The description is required; the wrapper rejects a bare name. If a spec or plan document already exists for this work, attach it as a project resource in the same step:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" add-project-resource "<team>" "<name>" "<url>" "<link label>"
```

Capture the project name.

_(A project joins the system by having a `.checklist.json` that names its Linear team + project. The spec ships bundled with the plugin in `spec/`.)_

## 5. Label selection

Run via Bash:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" list-labels "<team>"
```

Show the labels. Ask:

> *Use an existing label? (Or provide a new label name.)*

When they answer, check whether their response matches an existing label (case-insensitive). If it matches, use it. If it doesn't match, briefly confirm: *"Create new label '<X>'? (y/n, default y)"*. On yes, run:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" create-label "<team>" "<name>"
```

Capture the label name.

## 6. Capture mode

Ask:

> *Suggest new items when I notice todos in our chat? (y/n, default y)*

Map: yes → `ask`; no → `explicit`. See [Capture mode](${CLAUDE_PLUGIN_ROOT}/spec/capture-mode.md) for the semantics of each.

## 7. Initial slice

Run via Bash:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" list-open-slices "<team>" "<project>"
```

If there are open slices, show them. Ask:

> *Pick an existing slice? (Or provide a title for a new one.)*

If there are no open slices, ask:

> *What's the title of your first slice? (Or describe what you're working on and I'll suggest one.)*

Tip: for Personal-style buckets that don't transition slices, suggest a perpetual title like "Ongoing personal todos" if the user seems unsure.

When they answer, check whether their response matches an existing slice's identifier or title. If it matches, capture the identifier. If it doesn't match, treat it as a new slice title and run:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" create-issue "<team>" "<project>" "<title>" "<label>"
```

Capture the new identifier from the JSON output.

## 8. Migration scan

First, ask:

> *Scan for existing todos to bring into this slice? (y/n)*

If `n`, skip to step 9.

If `y`, scan the directory using Bash/Glob/Grep for likely todo storage (exclude `node_modules`, `.git`, `_archive`):

- `TODO.md`, `TODOS.md`, `Todo.md`, `tasks.md`, `TASKS.md` at any reasonable depth
- `STATUS.md` (often holds in-flight status)
- `docs/superpowers/plans/**/*.md` (plan files with unchecked items)
- `*.md` at the directory root (in case there's a notes file)

For each candidate file with `- [ ] ` lines, collect the items. For files without checkboxes, note the file but don't extract.

Show the user a brief inventory. If you found nothing, say so plainly ("Found no checkbox items to migrate.") and then ask:

> *Any other paths I should check?*

If they name paths, scan those and show what you found.

If items were found, walk through them grouped by source file. Default behavior: confirm-each. For bulk acceptance, the user can say "yes to all from this file" or similar — honor that.

For each accepted item:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" append-checkbox <slice-key> "<item text>"
```

After migration completes, for each source file you migrated items from, ask:

> *What should I do with `<file>`? (leave / annotate / archive / delete; default: leave)*

- **Leave**: do nothing.
- **Annotate**: prepend a header to the file:
  ```
  > **Note**: Items from this file have been migrated to the Linear slice tracker.
  > See: <slice issue URL>
  ```
- **Archive**: `mkdir -p _archive && mv <file> _archive/`
- **Delete**: confirm once more before doing it.

## 9. Write `.checklist.json`

Write to `<CWD>/.checklist.json` following the schema in [The .checklist.json file](${CLAUDE_PLUGIN_ROOT}/spec/the-checklistjson-file.md):

```json
{
  "team": "<team>",
  "project": "<project>",
  "label": "<label>",
  "current_slice_issue": "<slice-key>",
  "capture_mode": "<mode>"
}
```

Use the team captured in step 1, the project from step 4, the label from step 5, the slice key from step 7, and the capture mode from step 6.

## 10. Confirm

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/linear.py" get-issue <slice-key>` to fetch the slice's URL. Then display:

```
Onboarded <CWD>:
- Linear team: <team>
- Linear project: <project>
- Label: <label>
- Current slice: <slice-key> "<title>" — <url>
- .checklist.json written.
- Migrated <N> items from <M> source files (or "Skipped migration").

Try `/checklist:status` or just ask "what's on my plate" to see your current items.
```

## Error handling

- If any wrapper command exits non-zero, surface the error verbatim and stop. Don't retry.
- If the user wants to abort partway through (e.g., after creating a project but before writing `.checklist.json`), respect it — but warn that any Linear-side artifacts (project, label, slice) created during the partial run are now sitting in Linear and may need cleanup in the UI.
- Don't proceed past step 9 (write `.checklist.json`) without confirming all the data you've collected from the user.

## Relevant spec docs

- [Overview](${CLAUDE_PLUGIN_ROOT}/spec/overview.md) — what onboarding actually enables
- [Detection](${CLAUDE_PLUGIN_ROOT}/spec/detection.md) — how the system finds `.checklist.json`
- [The .checklist.json file](${CLAUDE_PLUGIN_ROOT}/spec/the-checklistjson-file.md) — schema and field semantics
- [Capture mode](${CLAUDE_PLUGIN_ROOT}/spec/capture-mode.md) — `ask` vs `explicit`
- [The linear.py wrapper](${CLAUDE_PLUGIN_ROOT}/spec/the-linearpy-wrapper.md) — full subcommand reference
- [Coexistence](${CLAUDE_PLUGIN_ROOT}/spec/coexistence.md) — how the system relates to `TODO.md` and plan files (relevant during migration scan)

---
name: setup
description: Bootstrap the personal checklist system (Failpunk Linear) in the current directory, including migration of existing todos
---

Onboard the user's current directory into the personal checklist tracking system. This drives a multi-step conversational flow with the user — pause at each question and wait for their answer; don't bulk-execute.

The team is always `Failpunk` (the only team in this v1 system) — don't ask about it.

All Linear interactions go through `~/.claude-adly/plugins/checklist/scripts/linear.py`.

## 1. Pre-flight check

Run via Bash:

```
python3 ~/.claude-adly/plugins/checklist/scripts/linear.py list-projects Failpunk
```

If the wrapper errors with "no Linear API key found", stop and tell the user:

> The Linear API key isn't set up. Once it is, re-run `/checklist:setup`.
>
> - Linear UI → Settings → API → Personal API keys → Create (in the `failpunkllc` workspace)
> - Then either:
>   - Add to `~/.zshrc`: `export LINEAR_FAILPUNK_API_KEY="lin_api_..."` and `source ~/.zshrc`
>   - OR save to `~/.config/checklist/api-key` with `chmod 600`

If the wrapper succeeds, hold the project list — you'll use it in step 4.

## 2. Detect existing config

Walk up from CWD looking for `.checklist.json` per the [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21) rules.

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

When they answer, check whether their response matches an existing project name (case-insensitive). If it matches, use it. If it doesn't match any existing project, briefly confirm: *"Create new project '<X>'? (y/n, default y)"*. On yes, draft a description per the [Project hygiene](https://linear.app/failpunkllc/document/project-hygiene-26c390f7c1ab) bar (what this is, where it lives on disk, how to pick it up cold), confirm the wording with the user, then run via Bash:

```
python3 ~/.claude-adly/plugins/checklist/scripts/linear.py create-project Failpunk "<name>" "<description>"
```

The description is required; the wrapper rejects a bare name. If a spec or plan document already exists for this work, attach it as a project resource in the same step:

```
python3 ~/.claude-adly/plugins/checklist/scripts/linear.py add-project-resource Failpunk "<name>" "<url>" "<link label>"
```

Capture the project name.

_(A project joins the system by having a `.checklist.json` that names its Linear team + project. The spec ships bundled with the plugin in `spec/`.)_

## 5. Label selection

Run via Bash:

```
python3 ~/.claude-adly/plugins/checklist/scripts/linear.py list-labels Failpunk
```

Show the labels. Ask:

> *Use an existing label? (Or provide a new label name.)*

When they answer, check whether their response matches an existing label (case-insensitive). If it matches, use it. If it doesn't match, briefly confirm: *"Create new label '<X>'? (y/n, default y)"*. On yes, run:

```
python3 ~/.claude-adly/plugins/checklist/scripts/linear.py create-label Failpunk "<name>"
```

Capture the label name.

## 6. Capture mode

Ask:

> *Suggest new items when I notice todos in our chat? (y/n, default y)*

Map: yes → `ask`; no → `explicit`. See [Capture mode](https://linear.app/failpunkllc/document/capture-mode-6103e77ae078) for the semantics of each.

## 7. Initial slice

Run via Bash:

```
python3 ~/.claude-adly/plugins/checklist/scripts/linear.py list-open-slices Failpunk "<project>"
```

If there are open slices, show them. Ask:

> *Pick an existing slice? (Or provide a title for a new one.)*

If there are no open slices, ask:

> *What's the title of your first slice? (Or describe what you're working on and I'll suggest one.)*

Tip: for Personal-style buckets that don't transition slices, suggest a perpetual title like "Ongoing personal todos" if the user seems unsure.

When they answer, check whether their response matches an existing slice's identifier or title. If it matches, capture the identifier. If it doesn't match, treat it as a new slice title and run:

```
python3 ~/.claude-adly/plugins/checklist/scripts/linear.py create-issue Failpunk "<project>" "<title>" "<label>"
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
python3 ~/.claude-adly/plugins/checklist/scripts/linear.py append-checkbox <slice-key> "<item text>"
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

Write to `<CWD>/.checklist.json` following the schema in [The .checklist.json file](https://linear.app/failpunkllc/document/the-checklistjson-file-42b14155210c):

```json
{
  "team": "Failpunk",
  "project": "<project>",
  "label": "<label>",
  "current_slice_issue": "<slice-key>",
  "capture_mode": "<mode>"
}
```

(Don't include `team` as a question — it's always `Failpunk` in v1.)

## 10. Confirm

Run `linear.py get-issue <slice-key>` to fetch the slice's URL. Then display:

```
Onboarded <CWD>:
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

- [Overview](https://linear.app/failpunkllc/document/overview-93132484f842) — what onboarding actually enables
- [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21) — how the system finds `.checklist.json`
- [The .checklist.json file](https://linear.app/failpunkllc/document/the-checklistjson-file-42b14155210c) — schema and field semantics
- [Capture mode](https://linear.app/failpunkllc/document/capture-mode-6103e77ae078) — `ask` vs `explicit`
- [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f) — full subcommand reference
- [Coexistence](https://linear.app/failpunkllc/document/coexistence-33eeefd6b24e) — how the system relates to `TODO.md` and plan files (relevant during migration scan)

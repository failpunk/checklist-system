Every onboarded directory has a `.checklist.json` file. Schema:

```json
{
  "team": "<team name>",
  "project": "<project name>",
  "label": "<label name>",
  "current_slice_issue": "ABC-N",
  "capture_mode": "ask"
}
```

| Field | Meaning |
| -- | -- |
| `team` | Linear team name (the team that holds this project's slices). |
| `project` | Linear project name within the team. |
| `label` | Linear label auto-applied to slice issues for this project. |
| `current_slice_issue` | Full Linear key for the active slice (e.g. `ABC-42`), or `null`. |
| `capture_mode` | `"ask"` (default) or `"explicit"`. Governs inferred captures only. |

## See also

* [Detection](./detection.md)
* [Capture mode](./capture-mode.md)

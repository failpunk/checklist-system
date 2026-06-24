Every onboarded directory has a `.checklist.json` file. Schema:

```json
{
  "team": "Failpunk",
  "project": "<project name>",
  "label": "<label name>",
  "current_slice_issue": "FAIL-N",
  "capture_mode": "ask"
}
```

| Field | Meaning |
| -- | -- |
| `team` | Linear team name. Always `Failpunk` in this user's setup. |
| `project` | Linear project name within the team. |
| `label` | Linear label auto-applied to slice issues for this project. |
| `current_slice_issue` | Full Linear key for the active slice (e.g. `FAIL-42`), or `null`. |
| `capture_mode` | `"ask"` (default) or `"explicit"`. Governs inferred captures only. |

## See also

* [Detection](https://linear.app/failpunkllc/document/detection-da35396daa21)
* [Capture mode](https://linear.app/failpunkllc/document/capture-mode-6103e77ae078)

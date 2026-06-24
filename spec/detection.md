When the user references checklist work, walk up from CWD looking for `.checklist.json`. Stop at `$HOME`. The nearest one wins (no merging).

The SessionStart hook prints the file's contents at session start and fetches the spec (this initiative's documents) from Linear. If you see that context loaded, the system applies. If not, the system silently doesn't apply for this directory — don't try to bootstrap unprompted.

When the system doesn't apply, existing project conventions (`TODO.md`, scattered notes, items in other Linear orgs) keep working as before.

## See also

* [The .checklist.json file](./the-checklistjson-file.md)
* [Coexistence](./coexistence.md)

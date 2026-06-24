Slice issue bodies follow a consistent layout enforced by the wrapper:

```markdown
- [ ] task one
- [ ] task two
- [x] task three (done)


# Plan content

[Free-form markdown: sections, decisions, pointers, anything `superpowers:writing-plans` would have produced as a separate plan file.]
```

Checkboxes always at the **top**; blank lines, then plan content below. Reason: the user reads on mobile; long plans above the checkboxes force scrolling.

`linear.py append-checkbox` automatically inserts new items at the end of the top checkbox block. When posting plan content via `linear.py set-body`, **preserve the top checkbox section** — don't replace the entire body or you'll wipe the checklist.

## See also

* [Slice state lifecycle](https://linear.app/failpunkllc/document/slice-state-lifecycle-c7e2df5dc679)
* [The linear.py wrapper](https://linear.app/failpunkllc/document/the-linearpy-wrapper-cf39f31f964f)

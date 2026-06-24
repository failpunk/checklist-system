**You are an agent reading this because you create or work on Failpunk projects. This document defines the minimum bar every project must meet, and the rules that keep project-level state honest. The checklist system keeps slices healthy; this spec keeps the projects above them from going hollow.**

## Why this exists

Observed 2026-06-12 (screen recording: [https://clipcabinet.com/s/cmqbhm5t7000n5wpap507b19j](<https://clipcabinet.com/s/cmqbhm5t7000n5wpap507b19j>)): nearly every Failpunk project had no description, no resources, Health "No updates", and a status that contradicted its own completion percentage (Nightshift sat in Backlog at 25% while its slice was In Progress; Notes Tab sat In Progress at 0%). A fresh agent session asked to "read from Linear and figure out what we're working on" could not orient. Root cause: slices have a state lifecycle and conventions; projects had neither, and `create-project` accepted a bare name.

## Two classes of project

1. **Real projects**: a body of work (an app, a system, a site). The full bar below applies.
2. **Machine hubs**: projects that exist as a destination for machine-generated issues (e.g. Agent Runs, written by the Nightshift runner). Lighter bar: a description stating what system writes to it and where that system lives. Exempt from spec/plan resources, status sync, and health updates.

A project's class is declared in its description. Default is real project.

## The bar (real projects)

Every real project carries, at all times:

1. **Description.** One short block answering three things: what this is, where it lives on disk (absolute path), and how to pick it up cold (the current slice, how to run it, or the doc to read first). Written at creation; updated when any of the three answers change.
2. **Spec/plan as Resources.** The design doc and/or implementation plan linked in the project's Resources section. These are living documents: when the plan changes, the linked doc is updated, not abandoned. Living Docs (Documentation System) also belong here.
3. **Accurate status.** Backlog / Planned / In Progress / Completed reflecting reality, kept honest by the sync rules below.

Explicitly NOT required: lead, target date, priority, milestones. Set them when useful; no rule enforces them.

## Status sync rules (promote-only)

Project status follows slice activity automatically, in one direction only:

* A slice entering In Progress (manually, or via check-item auto-transition, or sync-slice-state at session start) flips its project Backlog/Planned -> In Progress.
* All of a project's slices reaching Done does NOT auto-complete the project: the agent asks Justin before setting Completed.
* No automation ever demotes a project (In Progress -> Backlog) or cancels it. Mismatches in that direction are reported, not fixed.

Rationale: a mis-stated slice must not be able to silently bury or close a project.

## Health updates (milestones)

When a slice is marked Done, or a project changes state, the agent posts a short project update (2-4 sentences: what just landed, what is next). Tone: plain, concrete. This makes the Health column meaningful without daily chatter. Routine enforcement and drift detection belong to the project-manager Nightshift agent (FAIL-86), which audits all projects nightly, fixes what is mechanical under these rules, and reports judgment calls.

## Agent obligations

* **At project creation**: `create-project` requires a description (the wrapper enforces this). Write the three-part description at birth; if a spec or plan document already exists, attach it as a Resource in the same breath.
* **When a plan changes**: update the linked spec/plan doc rather than describing the change only in a slice body.
* **When working in a project that fails the bar**: fix mechanical gaps (status) directly; raise content gaps (missing description, stale spec) with Justin rather than silently inventing them.
* **Never** rewrite an existing human-written description without being asked.

## Borrowed from Linear Method (where it fits a solo-with-agents setup)

* Scope projects so a stage is completable in 1-3 weeks; if it cannot shrink, break it into stages rather than letting one project sprawl ([https://linear.app/method/scope-projects](<https://linear.app/method/scope-projects>)).
* Write issues, not user stories: slices already follow this; keep project descriptions equally direct.
* Momentum over deliberation: when project state is ambiguous, make the honest update now rather than deferring it ([https://linear.app/method/building-with-momentum](<https://linear.app/method/building-with-momentum>)).

## Tooling

`linear.py` subcommands serving this spec: `update-project` (description, status), `add-project-resource` (attach doc or URL), `post-project-update` (Health). See The [linear.py](<http://linear.py>) wrapper document for exact usage. Linear caps the project description field at 255 characters; put overflow detail in the project content (overview body) via `update-project --content`. File uploads attach to issues, comments, and documents only (not projects), per [https://linear.app/developers/how-to-upload-a-file-to-linear](<https://linear.app/developers/how-to-upload-a-file-to-linear>); project resources are links and documents.

## See also

* [Resuming work across sessions](https://linear.app/failpunkllc/document/resuming-work-across-sessions-0625ead5c70c) — the overview of how this bar, the status roll-up, and the project-manager agent let a cold session resume.


* Slice state lifecycle (slice-level transitions that feed the sync rules)
* The [linear.py](<http://linear.py>) wrapper (subcommand reference)
* Hard rules (confirmation rules; completion confirmations apply here too)

# Why this exists

## The granularity shift

Before AI, small, individually-scoped issues were the norm. Work was kept simple and small on
purpose — a human wrote every line, so a ticket was sized to what a person could hold in their
head and ship.

As we move to writing nearly zero code by hand and instead **orchestrating many changes at
once**, that model breaks down. Spinning up a swarm of small Linear issues for AI-driven work
becomes overwhelming and hard to track — the bookkeeping outgrows the building.

Taking inspiration from Claude's "superpowers" skills, which natively write work out as
**slices**, this system still leverages Linear but packs everything an individual slice needs
**inside a single Linear issue**: the checklist of steps and the plan both live in the issue
body. Each issue is therefore a much larger chunk that can be delivered in one pass, while
still holding a manageable amount of scope. Fewer, bigger, self-contained units instead of a
swarm of micro-tickets.

## What a slice is

**One Linear issue = one slice = one coherent chunk of work, with its checklist and plan
inside it.** The checkboxes are the steps; the body holds the plan and context. You track
progress at the slice level — a handful of live slices — not across dozens of tiny tickets.

## The second pillar: the agent always knows the plan

A slice isn't just a tidy container; it's also the agent's working memory. Coding agents are
stateless between sessions — each one starts cold and forgets what the project's plan was.
`TODO.md` files drift, and a session's own task list is ephemeral. So the slice is loaded into
context automatically at the start of **every** session (via a SessionStart hook), and the
agent reads and updates it as work happens. A few principles fall out of that:

- **Durable over ephemeral.** The slice is the backbone; a session's task list is scratch
  paper. Never track project-level work in something that disappears when the session ends.
- **One source of truth, two audiences.** You manage slices in Linear's web/mobile UI — read,
  scan, check off, reorder. The agent manages the *same* issues programmatically. No private
  copies that the other can't see.
- **Loaded every session, automatically.** Continuity comes from the hook, not from your
  discipline or the agent's luck. If it isn't loaded every session, it doesn't count.
- **Talk, don't type.** You mostly speak in natural language and the agent translates intent
  into Linear operations; the `/checklist:*` commands are escape hatches, not the main path.

## Why Linear (and not a bespoke tracker)

A custom tracker would mean building and maintaining a UI, mobile apps, search, and
notifications. Linear already *is* a system of record with a great human interface and a clean
API — so the agent gets a programmatic surface and you get a polished place to think, for free
(the free plan is plenty). The plugin is just the glue that makes an agent treat that system
of record as its working memory.

## The bet

Size the unit of work for an orchestrator, not a hand-coder — one self-contained slice instead
of a pile of tickets — and make that slice load itself every session. Then you spend your time
deciding *what* to build, not juggling a hundred issues or re-explaining where things stand.

---

*This is the maintainer's framing of the system; adapt it to your own workflow.*

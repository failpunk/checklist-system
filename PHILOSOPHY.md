# Why this exists

## The problem

Coding agents are **stateless between sessions**. Every new Claude session starts cold:
it doesn't remember what this project's todos are, what you decided last time, or what's
next. The usual patches don't hold:

- **`TODO.md` / plan files / scattered notes** drift out of date, live in different places
  per repo, and aren't reliably pulled into the agent's context.
- **The session's own task list** (e.g. TodoWrite) is ephemeral — it evaporates when the
  session ends, so it can't be the memory of the project.
- **Chat history** isn't a plan. Re-reading it every time is slow and lossy.

The result is re-briefing the agent, repeated questions, and work that quietly drifts from
what you actually wanted.

## The core idea

Keep the durable answer to **"what matters here and what's next"** in one place that is
*both* a good human interface *and* machine-readable — and load it automatically at the
start of every session. The agent should never have to be told the plan; it should already
know it.

Concretely: a project's high-level todos live as a **"slice" issue in Linear**. A tiny
`.checklist.json` onboards any directory. A SessionStart hook injects the current slice (and
the system's spec) into context the moment a session begins. The agent reads and updates the
slice through a thin wrapper as work happens.

## Principles

1. **Durable over ephemeral.** Project memory must outlive any single session. The slice is
   the backbone; the session's task list is scratch paper. Never trust ephemeral lists for
   project-level tracking.
2. **One source of truth, two audiences.** You manage todos in Linear's web/mobile UI —
   read, scan, check things off, reorder. The agent manages the *same* issues
   programmatically. Neither of you keeps a private copy that the other can't see.
3. **Loaded every session, automatically.** Continuity comes from the SessionStart hook, not
   from your discipline or the agent's luck. If it isn't loaded every session, it doesn't
   count.
4. **Cross-project, not per-repo silos.** "What's on my plate" spans many repos. Linear is
   one workspace across all of them; `.checklist.json` lets any directory opt in.
5. **Talk, don't type.** You mostly speak in natural language and the agent translates intent
   into Linear operations. Slash commands (`/checklist:*`) are escape hatches for explicit
   control, not the primary interface.
6. **The human stays in the loop without babysitting.** Because the truth lives in Linear,
   you can glance at progress on your phone or correct course in the UI — the agent picks it
   up next session. No standup, no status-doc maintenance.
7. **Lightweight and reversible.** It rides on a tool many people already use, works on
   Linear's free plan, and stores nothing exotic — a JSON file per repo and ordinary issues.

## Why Linear (and not a bespoke tracker)

Building a custom database would mean building (and maintaining) a UI, mobile apps, search,
notifications, and permissions. Linear already *is* a system of record with a great human
interface, a clean API, and mobile apps — so the agent gets a programmatic surface and you
get a polished place to think, for free. The plugin is just the glue that makes an agent
treat that system of record as its working memory.

## The bet

If the agent always knows the plan — because the plan loads itself every session and lives
where you can both see it — you spend your time deciding *what* to build, not re-explaining
*where things stand*.

---

*This is the maintainer's framing of the system; adapt it to your own workflow.*

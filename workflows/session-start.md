---
description: Run at the beginning of every Claude Code session to load context, surface ready work, and route multi-step requests through plan-and-execute.
---

# /session-start - Session Start

Every session starts cold. The bd memory layer holds non-obvious decisions, gotchas, and resolved blockers that don't live in git history. The ready queue surfaces what's in flight. The episodic-memory agent recovers context that would otherwise require re-exploration. Skipping this phase wastes the first 10–20 minutes of every session on ground already covered.

## When To Use

- First message of any new Claude Code session.
- Resuming after context compaction (conversation history cleared or truncated).
- User asks "what were we working on?" or "catch me up".
- Returning to a project after more than a few hours away.
- Starting work on a different machine (Windows ↔ Linux VPS).

## Workflow

### Phase 1: Prime context

1. Run `BEADS_DIR=~/.beads bd prime` — loads all persistent memory keys into context. Read every memory entry relevant to the current project and request.
2. Run `BEADS_DIR=~/.beads bd ready` — shows the current ready queue: available work, blockers, in-progress issues.
3. Present the output to the user as a digest: "X issues ready, Y in progress. Key memories: [list relevant ones]. Top blocker: [if any]."

### Phase 2: Continuity check

1. If the user references prior work, mentions a task by name, or if context appears missing after Phase 1, dispatch the `episodic-memory:search-conversations` agent with the user's terms (or inferred terms from the request).
2. Read the episodic results. Surface any decisions, blockers, or approaches found in prior sessions that are relevant to the current request.
3. If prior work was in progress and not closed in bd, note it explicitly: "bd shows [issue] in progress — is that still the focus?"

### Phase 3: Route the request

1. Assess the user's request. If it is multi-step (more than one logical action), touches more than two files, introduces an architectural change, or has unclear scope — trigger `workflows/plan-and-execute.md`. Do not improvise a procedure when a workflow exists.
2. If the request is single-step and bounded, proceed directly. Keep `workflows/code-writing.md` in scope for any code change.
3. State the routing decision explicitly: "This is a [single-step / multi-step] request — [proceeding directly / entering plan-and-execute]."

## Quality Guidelines

> [!CAUTION]
> **BLOCKING STEP.** If `bd ready` errors with "no beads database found", set `BEADS_DIR=~/.beads` before retrying. Do not proceed with implementation until bd resolves. A missing db means memory and issue state are inaccessible — proceeding without it risks duplicate work and lost context.

- MUST: read every memory pointer surfaced by `bd prime` that is relevant to the current request before writing a single line of code or creating a plan.
- MUST: complete Phase 1 before Phase 2. Do not skip to episodic search if bd has not loaded.
- SHOULD: skim the top 5 `bd ready` issues even when the user has a specific request — they may be blocking dependencies or closely related work.
- SHOULD: if Phase 3 routes to plan-and-execute, do NOT begin `EnterPlanMode` until Phase 1 and Phase 2 are complete. The plan must incorporate persisted context.

## References

- `CLAUDE.md` — `## Standing Instructions` (all rules; note: #5 session close, #6 permanent orchestrator)
- `workflows/plan-and-execute.md` — triggered by Phase 3 for multi-step requests
- `agents/morning-briefing.md` — agent prompt file (exists); the scheduled task itself was deleted 2026-05-05, so the agent prompt is dormant unless re-scheduled via the `schedule` skill

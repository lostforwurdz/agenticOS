---
name: session-prime
description: >-
  Parallel session warm-up chain. Fans out bd prime, bd ready, git fetch,
  episodic-memory recap, and VPS parity check in a single dispatch.
  Invoke at the start of any session for a full context restore — turns
  session start from a memory load into a coordinated context warm-up.
  Surfaces cross-machine drift (Windows ↔ Linux VPS) within seconds rather
  than discovering it mid-task.
---

# Session Prime

Parallel session warm-up. Fans out five context sources simultaneously, then synthesizes a single briefing paragraph.

## Trigger

Invoke when the `SessionStart` hook fires (first message of any session or after compaction), or manually when resuming after interruption.

## Phase 1 — Parallel Fan-out

> [!CAUTION]
> **BLOCKING STEP.** Dispatch all 5 in a SINGLE message with multiple Task tool calls. Do not dispatch sequentially — that defeats the parallel warm-up.

| Dispatch | Type | Output |
|---|---|---|
| `bd prime` | Bash | Persistent memories + ready queue |
| `bd ready` | Bash | Open work items, priority queue |
| `git fetch --all` (current repo) | Bash | Remote tracking refs updated |
| `vps-sync` agent | Task tool | VPS ↔ local parity report |
| `episodic-memory:search-conversations` (query: "yesterday OR last session") | Task tool | Prior-session summary |

Wait for ALL 5 to complete before proceeding to Phase 2.

## Phase 2 — Synthesis (sequential)

Wait for Phase 1 to complete. Orchestrator synthesizes all 5 outputs into a single briefing paragraph (under 100 words) covering: open work, cross-machine drift, prior-session blockers, and repo state. Output directly to chat — no file write required.

## Verification

- [ ] All 5 Phase 1 outputs surfaced.
- [ ] Synthesized briefing in chat, under 100 words.
- [ ] Cross-machine drift and critical blockers called out explicitly.

## References

- `workflows/session-start.md` — full session boot procedure this skill accelerates
- `agents/vps-sync.md` — VPS parity check agent
- `agents/morning-briefing.md` — scheduled daily briefing agent

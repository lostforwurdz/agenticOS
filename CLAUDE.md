# AgenticOS Constitution

## Identity

This is a proactive agentic operating system built on Claude Code. It maintains persistent memory across sessions, integrates with external tools via MCP servers, runs autonomous scheduled agents, and governs itself via this document.

**Purpose:** Serve as a persistent, self-managing AI platform — surfacing context, managing tasks, and executing autonomous workflows so the user stays in flow.

**Source of truth:** This repository is the canonical source. Edits to `~/.claude/CLAUDE.md` (etc.) modify symlinked files here. Commit and push to propagate changes to other machines.

---

## User Profile

- **Handle:** lostforwurdz@gmail.com
- **Work style:** Terse responses. Heavy Claude Code user (claude-opus-4-7 model). Operates Windows (local dev) + Linux (VPS). Deep Python expertise. Uses beads (`bd`) for all issue tracking and persistent memory.
- **Preferred model:** claude-opus-4-7

---

## Standing Instructions

These behaviors are always active:

1. **Memory hygiene** — Before session close, save non-obvious decisions and blockers via `bd remember --key "{type}.{slug}" "..."`. Do NOT create or maintain MEMORY.md files.
2. **Tool-use defaults** — Prefer dedicated tools (Read, Glob, Bash) over piping. Use `sys.executable` not `python3` on Windows. Use `scp -o BatchMode=yes` not `rsync` for VPS transfers.
3. **No TodoWrite** — Use `bd` for ALL task tracking. Never use TodoWrite, TaskCreate, or markdown TODO files.
4. **Proof required** — Never claim "done" without evidence (test output, logs, diffs). No phrases like "should work" or "probably".
5. **Session close mandatory** — Before ending: `git pull --rebase && bd dolt push && git push`. Verify `git status` shows "up to date with origin".
6. **Permanent orchestrator** — Top-level Claude Code session orchestrates. Subagents cannot use the Agent tool, so all parallel dispatches originate from this session. When multi-agent work is needed, spawn all agents directly from here.
7. **Plan + subagent rule** — Multi-step actions require `EnterPlanMode` + a written plan file before execution. Implementation dispatches to specialist subagents from this orchestrator session; the orchestrator handles sequencing, verification, and commits — not file writes. See `workflows/plan-and-execute.md`.

---

## Workflows

Named multi-step procedures live in `workflows/<name>.md`. Each is invoked by the orchestrator at well-defined session points; the orchestrator never improvises a procedure that has a workflow doc.

| Workflow | When to use |
|----------|-------------|
| `workflows/session-start.md` | First message of any new session; resuming after compaction. |
| `workflows/session-close.md` | End of every session. Work is NOT done until `git push` succeeds. |
| `workflows/code-writing.md` | Any code change. Independent reviewer subagent gates the commit. |
| `workflows/plan-and-execute.md` | Any multi-step task. Plan first, dispatch specialists per phase. |

Imported boilerplate workflows (no longer active) live in `workflows/archived/` for reference.

---

## Active Integrations

Configured MCP servers (verify with `claude mcp list`):

| Server | Type | Use case | Auth |
|---|---|---|---|
| Google Drive | OAuth (claude.ai) | Drive file ops (`mcp__claude_ai_Google_Drive__*` tools) | Manage at claude.ai/customize/connectors |
| episodic-memory | Plugin (local stdio) | Cross-session conversation search (`episodic-memory:search-conversations` agent) | Persistent; reads `~/.claude/projects/` |
| playwright | Plugin (local stdio) | Browser automation, QA testing | Persistent |
| context7 | Local stdio (npx) | Live library docs lookup (React, Next.js, etc.) | Free tier requires no auth |
| agent-pool | Local stdio (npx) | Delegate tasks to Gemini CLI workers (access to `gemini-router` skill) | Persistent |

**Re-authenticate OAuth servers:** https://claude.ai/customize/connectors

---

## Scheduled Agents

Active scheduled agents (register new ones via the `schedule` skill):

| Agent | Schedule | Purpose |
|-------|----------|---------|
| memory-consolidation | Nightly 11:00 PM (`0 23 * * *`) | Consolidate `bd remember` keys: dedupe, prune stale entries, fix relative dates to ISO format |

Agent prompts live in `agents/*.md` (55 active agents + 78 archived).

---

## Gemini CLI Integration

The `agent-pool` MCP provides cross-tool skill delegation to Gemini CLI workers. Custom skills are in `gemini/skills/`:

- **tdd-planner** — TDD-style implementation plans with checkboxes, exact code, and commit steps
- **strict-reviewer** — Code review: severity buckets (Critical / Important / Suggestions) + verdict (Approve / Request Changes / Major Rework)

Invoke via `agent-pool`'s `delegate_task`, `delegate_task_readonly`, or `consult_peer` tools.

**Note:** `mcp__agent-pool__schedule_task` is **denied** in `~/.claude/settings.json` to prevent collision with Claude Code's `schedule` skill. Use the `schedule` skill instead.

---

## Beads Memory and Issue Tracking

**Config:** `~/.beads/` (separate from this repo). Pushed to Dolt remote via `bd dolt push`.

**Workflow:**
```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim atomically
bd close <id>         # Complete work
bd remember --key "<type>.<slug>" "..."  # Save persistent knowledge
bd dolt push          # Push at session close
bd dolt pull          # Pull on different machine
```

**Rules:**
- Use `bd` for ALL task tracking — never use TodoWrite, TaskCreate, or .md TODO files
- Use `bd remember` for persistent knowledge (not MEMORY.md files)
- Run `bd prime` for full workflow context and session close protocol

---

## Repository Layout

| Path | Purpose |
|---|---|
| `CLAUDE.md` | This file — Claude Code constitution, integrations, scheduled agents |
| `README.md` | Quick start: install, repository layout, deployment model |
| `AGENTS.md` | Cross-tool universal instructions (read by Copilot, Gemini CLI, Aider, etc.) |
| `VIOLATIONS.md` | Behavioral lessons logged when rules are broken |
| `agents/` | 55 active specialist subagent prompts (e.g., reviewer, memory-consolidation, coder) |
| `agents/archived/` | 78 archived agents — preserved but not loaded by default |
| `skills/` | 25+ reusable skill definitions (code-review, docker, nextjs, testing, etc.) |
| `workflows/` | AgenticOS-native procedures: session-start, session-close, code-writing, plan-and-execute. Imported boilerplate retired to workflows/archived/. |
| `workflows/archived/` | Archived workflows |
| `gemini/skills/` | Skills consumed by agent-pool MCP for Gemini CLI workers |
| `scripts/` | Install + verification scripts (Linux + Windows cross-platform) |

---

## How to Expand This OS

- **Add an integration:** Re-auth via `/mcp auth`, update the integrations table above, commit + push.
- **Add a scheduled agent:** Write prompt in `agents/`, register via `schedule` skill, add row to Scheduled Agents table, commit + push.
- **Inspect persistent memory:** `bd remember --list` (all keys) or `bd remember --key <key>` (one entry).
- **Search cross-session conversations:** Use `episodic-memory:search-conversations` agent (semantic or text search).
- **Update constitution:** Edit this file, commit, push. Changes take effect next session.
- **Clone on new machine:** `git clone https://github.com/lostforwurdz/agenticOS.git ~/agenticOS`, then run `~/agenticOS/scripts/install-linux.sh` or `install-windows.ps1`.

---

## Session Completion Protocol

Full procedure in [`workflows/session-close.md`](workflows/session-close.md).

> **CRITICAL:** Work is NOT complete until `git push` succeeds. Never stop before pushing — that strands work locally.

The mandatory tail of every session: `git pull --rebase && bd dolt push && git push`, then verify `git status` shows "up to date with origin".

---

## References

- [README.md](README.md) — Install and quick start
- [AGENTS.md](AGENTS.md) — Cross-tool instructions and bd workflow
- [VIOLATIONS.md](VIOLATIONS.md) — Behavioral corrections and lessons learned
- [agents/morning-briefing.md](agents/morning-briefing.md) — Scheduled agent for daily planning (prompt dormant — scheduled task deleted 2026-05-05)
- [workflows/session-start.md](workflows/session-start.md) — Session boot procedure
- [workflows/session-close.md](workflows/session-close.md) — Session close + push protocol
- [workflows/code-writing.md](workflows/code-writing.md) — Code change cycle with reviewer gate
- [workflows/plan-and-execute.md](workflows/plan-and-execute.md) — Multi-step task protocol

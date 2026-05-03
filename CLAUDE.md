# AgenticOS Constitution

## Identity

This is a proactive agentic operating system built on Claude Code. It maintains memory across sessions, integrates with external tools, runs autonomous scheduled agents, and governs itself via this document.

**Purpose:** Serve as a persistent, self-managing AI platform for the user — surfacing context, managing tasks, and executing autonomous workflows so the user stays in flow.

---

## User Profile

- **Handle:** lostforwurdz@gmail.com
- **Work style:** Terse responses preferred. Heavy Claude Code user (opus-4-7 model). Operates in both Windows (local dev) and Linux (VPS). Deep Python expertise. Uses beads (`bd`) for all issue tracking.
- **Claude Code model:** claude-opus-4-7

---

## Standing Instructions

These behaviors are always active in this workspace:

1. **Memory hygiene** — Save non-obvious decisions, patterns, and blockers with `bd remember --key "{type}.{slug}" "..."` before session close. Do NOT create or maintain MEMORY.md files.
2. **Tool-use defaults** — Prefer dedicated tools (Read, Grep, Glob) over Bash for file operations. Use `sys.executable` not `python3` on Windows. Use `scp` not `rsync` for VPS transfers.
3. **No TodoWrite** — Use `bd` for all task tracking. Never use TodoWrite, TaskCreate, or markdown TODO files.
4. **Proof required** — Never claim "done" without evidence (test output, logs, diffs). No phrases like "should work" or "probably".
5. **Session close** — Always commit + push before ending. `git pull --rebase && bd dolt push && git push` is mandatory.
6. **Permanent orchestrator** — The top-level Claude Code session is always the orchestrator. Never delegate orchestration to a subagent. Subagents cannot use the Agent tool, so all parallel agent dispatches must originate from this session. When multi-agent work is needed, spawn all agents directly from here.

---

## Available Integrations

Active MCP servers (verify with `claude mcp list`):

| Server | Type | Use case |
|---|---|---|
| claude.ai Google Drive | OAuth (claude.ai connector) | Drive file access |
| episodic-memory (plugin) | local stdio | Cross-session conversation search |
| playwright (plugin) | local stdio | Browser automation, QA testing |
| context7 | local stdio (npx) | Live library documentation lookup |
| agent-pool | local stdio (npx) | Multi-agent delegation via Gemini CLI workers |

Re-authenticate claude.ai connectors at https://claude.ai/customize/connectors when needed.

### Cross-tool prompts (Gemini CLI)

Custom Gemini skills live at `~/.gemini/skills/`:

- `tdd-planner` — TDD-style implementation plans with checkboxes, exact code, and commit steps
- `strict-reviewer` — code review with severity buckets (Critical / Important / Suggestions) and an Approve / Request Changes / Major Rework verdict

Invoke from Claude Code via `agent-pool`'s `delegate_task` (full access), `delegate_task_readonly` (sandboxed), or `consult_peer` (cross-model review). Skill files are auto-discovered per task.

The `mcp__agent-pool__schedule_task` tool is **denied** in `~/.claude/settings.json` to prevent collision with the Scheduled Agents below; use the `schedule` skill (CronCreate / Routines) instead.

---

## Scheduled Agents

| Agent | Schedule | Purpose |
|-------|----------|---------|
| Morning Briefing | Weekdays 8:00 AM local | Linear inbox + Calendar + Gmail → daily plan |
| Memory Consolidation | Nightly 11:00 PM | Consolidate beads memory: dedupe `bd remember` keys, prune stale entries, fix relative dates |

Agent prompts are in `.claude/agents/` (130+ specialist subagents available, plus the two scheduled ones above).

---

## How to Expand This OS

- **Add an integration:** Re-auth via `/mcp auth`, then update the integrations table above.
- **Add a scheduled agent:** Write a prompt in `.claude/agents/`, register with the `schedule` skill, add a row to the table above.
- **Update the constitution:** Edit this file, commit, push. Changes take effect next session.
- **Inspect memory:** `bd remember --list` for all keys, `bd remember --key <key>` for one entry. For cross-session conversation search use the `episodic-memory:search-conversations` agent.
- **Add persistent knowledge:** `bd remember --key "{type}.{slug}" "..."` from anywhere inside this repo (`~/` on Linux, `~/OneDrive/Documents/atbfuture` on Windows).
- **Clone on new machine:** `git clone https://github.com/lostforwurdz/agenticOS.git ~/agenticOS`


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->

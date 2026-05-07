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
3. **No TodoWrite** — Use `bd` for ALL task tracking. Never use TodoWrite, TaskCreate, or markdown TODO files. (now harness-enforced via permissions.deny in ~/.claude/settings.json)
4. **Proof required** — Never claim "done" without evidence (test output, logs, diffs). No phrases like "should work" or "probably".
5. **Session close mandatory** — Before ending: `git pull --rebase && bd dolt push && git push`. Verify `git status` shows "up to date with origin".
6. **Permanent orchestrator** — Top-level Claude Code session orchestrates. Subagents cannot use the Agent tool, so all parallel dispatches originate from this session. When multi-agent work is needed, spawn all agents directly from here. (now partially harness-enforced via PreToolUse hook on Write/Edit and UserPromptSubmit advisory in ~/.claude/settings.json)
7. **Plan + subagent rule** — Multi-step actions require `EnterPlanMode` + a written plan file before execution. Implementation dispatches to specialist subagents from this orchestrator session; the orchestrator handles sequencing, verification, and commits — not file writes. See `workflows/plan-and-execute.md`. (now partially harness-enforced via PreToolUse hook on Write/Edit and UserPromptSubmit advisory in ~/.claude/settings.json)

---

## Workflows

Named multi-step procedures live in `workflows/<name>.md`. Each is invoked by the orchestrator at well-defined session points; the orchestrator never improvises a procedure that has a workflow doc.

| Workflow | When to use |
|----------|-------------|
| `workflows/session-start.md` | First message of any new session; resuming after compaction. Phase 1.5 dispatches `violations-enforcer` on non-trivial first prompts. |
| `workflows/session-close.md` | End of every session. Work is NOT done until `git push` succeeds. |
| `workflows/code-writing.md` | Any code change. Independent reviewer subagent gates the commit. |
| `workflows/plan-and-execute.md` | Any multi-step task. Plan first, dispatch specialists per phase. |
| `workflows/full-audit.md` | Parallel multi-agent audit (9 agents) → consolidated FIXES.md. |
| `workflows/release-prep.md` | 6-phase release cycle: full-audit → fixes → tests → security → deploy validation → release PR. Phase 4 uses `security-gate` chain. |
| `workflows/bug-fix.md` | TDD bug-fix chain: failing repro test → fix → regression check → optional UI verify. Phase 2.5 auto-escalates to `dual-review` for auth/payment/encryption/migration paths. |
| `workflows/new-feature.md` | TDD feature chain: failing tests → implementation (stack-routed) → regression → optional UI verify. |
| `workflows/pre-commit.md` | Batch pre-commit gate: parallel reviewer + tester on staged files. |
| `workflows/memory-stack-recovery.md` | Per-layer recovery runbook for the 6-layer memory stack. Triggered by red layers from `scripts/stack-health.py`. |

Imported boilerplate workflows (no longer active) live in `workflows/archived/` for reference.

---

## Skills

Registered skills in three forms:

**Chain skills (in `skills/<name>/SKILL.md` — slash-invocable):**
- `gemini-router` — when and how to invoke Gemini via agent-pool
- `security-gate` — parallel security chain (semgrep + codeql + supply-chain + insecure-defaults + security-auditor → differential-review consolidator)
- `content-pr` — sequential content gate (seo → ui → a11y → reviewer)
- `dep-health` — parallel dependency audit (dependency-manager + supply-chain + compliance → debugger consolidator)
- `dual-review` — parallel high-stakes review (local reviewer + Gemini strict-reviewer via gemini-router)
- `session-prime` — parallel session warm-up chain
- `pr-ready` — sequential pre-merge gate composite
- `schema-change` — DB migration safety gate (parallel + sequential)

**Security skills (existing, in `skills/<name>/SKILL.md` — slash-invocable):**
- `codeql`, `semgrep`, `differential-review`, `insecure-defaults`, `sarif-parsing`, `supply-chain-risk-auditor`

**Pointer skills (loose `.md` files at `skills/` root — point to registered `engineering:*` skills):**
- `code-review` → `engineering:code-review`
- `debug` → `engineering:debug`
- `testing` → `engineering:testing-strategy`

**Topic references (in `skills/references/` — not slash commands, general reference material):**
`api-design`, `docker`, `mobile`, `nextjs`, `performance`, `react-patterns`, `security`, `tailwind`

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
| stack-health-cron | Nightly 11:30 PM (`30 23 * * *`) | Run `scripts/stack-health.py`, persist to `bd remember --key stack-health.<date>`, auto-file bd issue on consecutive red nights |
| dep-health-weekly | Mondays 09:00 (`0 9 * * 1`) | `/dep-health` chain on active project repos |
| full-audit-weekly | Sundays 10:00 (`0 10 * * 0`) | `/full-audit` workflow on active project |
| agent-hygiene-monthly | 1st of month 09:00 (`0 9 1 * *`) | Catalog hygiene scan (broken refs, weak descriptions) |
| stale-branch-sweep | Fridays 08:00 (`0 8 * * 5`) | Report-only stale-branch audit (no auto-prune) |

Agent prompts live in `agents/*.md` (42 active agents + 91 archived).

---

## Active Hooks

Hook configuration lives in `~/.claude/settings.json` (per-machine, NOT in this repo). On a fresh machine, replicate:

| Event | Matcher | Behavior |
|-------|---------|----------|
| SessionStart | "" | Run `bd prime` |
| PreCompact | "" | Run `bd prime` |
| UserPromptSubmit | "" | Pattern-match prompt for multi-step keywords; inject plan-and-execute reminder |
| PreToolUse | Write\|Edit\|MultiEdit | Block if no plan file exists in `~/.claude/plans/` (Standing Instruction #7 enforcement) |
| PreToolUse (advisory) | Write\|Edit\|MultiEdit | If file path matches `auth\|payment\|encrypt\|secret`, advise running `/security-gate` before merge |
| PreToolUse (advisory) | Write\|Edit\|MultiEdit | If file path matches `migrations/\|schema.ts\|drizzle/\|*.sql`, advise running `/schema-change` before merge |
| PreToolUse (advisory) | Write\|Edit\|MultiEdit | If file path matches `package.json\|requirements.txt\|pyproject.toml\|go.mod\|Cargo.toml`, advise running `/dep-health` |
| Stop | "" | Warn if uncommitted or unpushed git work (Standing Instruction #5 enforcement) |

`permissions.deny: ["TodoWrite"]` is also set, enforcing Standing Instruction #3.

**Cross-machine note:** settings.json is per-machine. To replicate on the Linux VPS, copy the same JSON structure into `~/.claude/settings.json` there. Cron expressions and paths use forward slashes; works on both platforms.

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
| `agents/` | 42 active specialist subagent prompts (13 stack specialists retired 2026-05-05) |
| `agents/archived/` | 91 archived agents — preserved but not loaded by default |
| `skills/` | Reusable skills in three forms: chain skills (`<name>/SKILL.md` dirs, slash-invocable), pointer `.md` files (point to `engineering:*` registered skills), and `references/` subfolder (topic references, not slash commands). |
| `workflows/` | AgenticOS-native procedures: session-start, session-close, code-writing, plan-and-execute, full-audit, release-prep, bug-fix, new-feature, pre-commit. Imported boilerplate retired to workflows/archived/. |
| `workflows/archived/` | Archived workflows |
| `gemini/skills/` | Skills consumed by agent-pool MCP for Gemini CLI workers |
| `scripts/` | Install + verification scripts (Linux + Windows cross-platform); includes `check-skill-pointers.sh` |

---

## How to Expand This OS

- **Add an integration:** Re-auth via `/mcp auth`, update the integrations table above, commit + push.
- **Add a scheduled agent:** Write prompt in `agents/`, register via `schedule` skill, add row to Scheduled Agents table, commit + push.
- **Inspect persistent memory:** `bd remember --list` (all keys) or `bd remember --key <key>` (one entry).
- **Search cross-session conversations:** Use `episodic-memory:search-conversations` agent (semantic or text search).
- **Update constitution:** Edit this file, commit, push. Changes take effect next session.
- **Clone on new machine:** `git clone https://github.com/lostforwurdz/agenticOS.git ~/agenticOS`, then run `~/agenticOS/scripts/install-linux.sh` or `install-windows.ps1`.
- **Verify plugin shadowing:** run `bash ~/agenticOS/scripts/check-skill-pointers.sh` — exits non-zero if any thin pointer skill cites a plugin that's not installed.

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
- [workflows/full-audit.md](workflows/full-audit.md) — Parallel 9-agent audit → consolidated FIXES.md
- [workflows/release-prep.md](workflows/release-prep.md) — 6-phase release cycle
- [workflows/bug-fix.md](workflows/bug-fix.md) — TDD bug-fix chain
- [workflows/new-feature.md](workflows/new-feature.md) — TDD feature chain
- [workflows/pre-commit.md](workflows/pre-commit.md) — Batch pre-commit gate
- [workflows/memory-stack-recovery.md](workflows/memory-stack-recovery.md) — Per-layer recovery runbook for the 6-layer memory stack
- [scripts/stack-health.py](scripts/stack-health.py) — Health probe wired into `workflows/session-start.md` Phase 1

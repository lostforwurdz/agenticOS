# AgenticOS

A proactive agentic operating system for Claude Code. Maintains persistent memory across sessions, integrates with external tools, runs autonomous scheduled agents, and governs itself via constitution.

**Status:** Production

---

## What It Is

AgenticOS is a bootstrap kit for Claude Code on Windows and Linux. When cloned into `~/agenticOS`, the install scripts symlink constitution files (`CLAUDE.md`, `AGENTS.md`, etc.), 55+ specialist agents, 25+ reusable skills, and workflows into `~/.claude/` and `~/.gemini/`. 

Edit anywhere (`~/.claude/CLAUDE.md` or `~/agenticOS/CLAUDE.md` are the same file via symlink). Changes propagate across machines via `git push` + `git pull` and `bd dolt push` + `bd dolt pull` (for persistent memory stored separately in `~/.beads/`).

---

## Quick Start

### Install on Linux

```bash
git clone https://github.com/lostforwurdz/agenticOS.git ~/agenticOS
~/agenticOS/scripts/install-linux.sh
```

Idempotent. Symlinks replace existing symlinks; real files are backed up to `~/.claude/_pre-symlink-backup-<timestamp>/`.

### Install on Windows

**Prerequisite:** Enable Developer Mode (Settings → Privacy & security → For developers → Developer Mode = ON) so symlinks can be created without admin elevation.

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\agenticOS\scripts\install-windows.ps1"
```

Idempotent. Same backup behavior as Linux.

### Verify Installation

```bash
~/agenticOS/scripts/verify-hooks.sh
```

Static check: `~/.claude/settings.json` has expected hooks wired. Prints live-test instructions at end.

---

## Repository Layout

| Path | Contents |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Claude Code constitution — identity, standing rules, integrations, scheduled agents, session protocol |
| [`AGENTS.md`](AGENTS.md) | Cross-tool universal instructions (read by Copilot, Gemini CLI, Aider, etc.) — bd workflow and shell best practices |
| [`README.md`](README.md) | This file — install, repo layout, development model |
| [`VIOLATIONS.md`](VIOLATIONS.md) | Behavioral corrections logged when rules are broken |
| [`agents/`](agents/) | 55 active specialist subagent definitions (e.g., morning-briefing, memory-consolidation, react-specialist, fastapi-developer) |
| [`agents/archived/`](agents/archived/) | 78 archived agents — preserved but not loaded by default |
| [`skills/`](skills/) | 25+ reusable skill definitions (code-review, docker, nextjs, security, testing, etc.) plus subdirectories (codeql, differential-review, semgrep, sarif-parsing, supply-chain-risk-auditor, insecure-defaults) |
| [`workflows/`](workflows/) | Multi-step workflow definitions (plan-compound.md, review-compound.md, work.md, explore.md, cycle.md, resolve_pr.md) |
| [`workflows/archived/`](workflows/archived/) | Archived workflows |
| [`gemini/skills/`](gemini/skills/) | Skills for Gemini CLI workers (tdd-planner, strict-reviewer) — consumed by agent-pool MCP |
| [`scripts/`](scripts/) | Install + verification (bash + PowerShell, cross-platform) |

---

## Core Concepts

### Constitution over Conventions

`CLAUDE.md` is the single source of truth. It defines:
- Standing rules (memory hygiene, tool defaults, proof requirement, session close protocol)
- Active integrations (MCP servers, OAuth connectors)
- Scheduled agents (morning briefing, memory consolidation)
- Permanent orchestrator pattern (top-level session only, no subagent delegation)

Read `CLAUDE.md` at the start of each session.

### Symlink Strategy

Install scripts create symlinks from `~/.claude/` and `~/.gemini/` into `~/agenticOS/`. This means:
- You can edit `~/.claude/CLAUDE.md` in your IDE; changes write to `~/agenticOS/CLAUDE.md`
- You can edit `~/agenticOS/CLAUDE.md` directly; `~/.claude/` reads the same file
- Commit from `~/agenticOS/`, push, then `git pull` on the other machine
- Both Linux and Windows use the same workflow: one source of truth

### Persistent Memory vs. Configuration

- **Configuration** (`CLAUDE.md`, `AGENTS.md`, agents, skills, workflows): tracked in this repo. Sync via `git push` + `git pull`.
- **Persistent memory** (`bd remember` keys, issue tracking): stored in `~/.beads/`. Sync separately via `bd dolt push` + `bd dolt pull` at session boundaries.

Example session close:
```bash
git pull --rebase
bd dolt push  # Push memory
git push      # Push config changes
```

### Scheduled Agents

Two agents run on schedule (set up during install):

1. **morning-briefing** — Weekdays 8 AM. Pulls `bd ready` queue, due/overdue items, and optional calendar/email/issue MCPs → daily plan.
2. **memory-consolidation** — Nightly 11 PM. Consolidates `bd remember` keys (dedupe, prune stale, convert relative dates to ISO).

Add more via the `schedule` skill and register in `CLAUDE.md`.

---

## Development

### Add a Specialist Agent

Create `agents/my-agent.md`:

```markdown
---
name: my-agent
description: Short description
model: sonnet (or haiku/opus)
---

# My Agent

Instructions for what this agent does.
```

Register in a scheduled hook or the `schedule` skill.

### Add a Reusable Skill

Create `skills/my-skill.md` following the existing format (e.g., `skills/code-review.md`). Document:
- What it does
- When to use it
- Prerequisites / environment
- Invocation example

### Add a Workflow

Create `workflows/my-workflow.md`. Workflows are multi-step definitions that agents follow. See `workflows/plan-compound.md` for structure.

---

## Deployment Model

### Source of Truth

The repo is the canonical source. When you edit `~/.claude/CLAUDE.md`:
1. Changes write to `~/agenticOS/CLAUDE.md` via symlink
2. You commit + push from `~/agenticOS/`
3. On a different machine: `git pull` updates `~/agenticOS/`, which updates `~/.claude/` via symlink

### Cross-Machine Sync

```bash
# On machine A: commit + push config changes, push memory
git pull --rebase
bd dolt push
git push

# On machine B: pull config, pull memory
git pull
bd dolt pull
```

### Installation Idempotency

Both `install-linux.sh` and `install-windows.ps1` are safe to re-run:
- Already-correct symlinks: skipped
- Wrong symlinks: replaced
- Real files with content: backed up to `_pre-symlink-backup-<timestamp>/`, then symlinked

---

## External Integrations

AgenticOS integrates with:

- **Claude Code** — The harness that runs this
- **Google Drive** (OAuth via claude.ai) — File operations
- **Episodic Memory** (MCP plugin) — Cross-session conversation search
- **Playwright** (MCP plugin) — Browser automation
- **Context7** (local MCP) — Live library documentation
- **Agent Pool** (local MCP) — Delegate to Gemini CLI workers
- **Beads** (`bd` CLI) — Issue tracking + persistent memory (separate from this repo)

Configure MCPs via `claude mcp list` and re-auth OAuth servers at https://claude.ai/customize/connectors.

---

## Beads Workflow

Beads (`bd`) is the issue tracker and persistent memory store (separate from this repo):

```bash
bd ready                 # Find available work
bd show <id>             # View issue
bd update <id> --claim   # Claim atomically
bd close <id>            # Complete
bd remember --key "<key>" "value"  # Save persistent knowledge
bd dolt push             # Push to remote
bd dolt pull             # Pull on different machine
```

Rules:
- Use `bd` for ALL task tracking (no TodoWrite, TaskCreate, .md TODOs)
- Use `bd remember` for persistent knowledge (no MEMORY.md files)
- Run `bd prime` for full context and session close protocol

---

## Standing Rules

All Claude Code sessions in this OS follow these:

1. **Memory hygiene** — Save non-obvious decisions via `bd remember --key "{type}.{slug}" "..."` before session close
2. **Tool defaults** — Prefer Read/Glob/Bash over piping. Use `sys.executable` on Windows, `scp -o BatchMode=yes` for VPS
3. **No TodoWrite** — Use `bd` for all task tracking
4. **Proof required** — Never claim "done" without evidence (test output, logs, diffs)
5. **Session close mandatory** — `git pull --rebase && bd dolt push && git push` before exiting
6. **Permanent orchestrator** — Top-level Claude Code session only. Subagents cannot dispatch other agents

See `CLAUDE.md` for details.

---

## References

- [`CLAUDE.md`](CLAUDE.md) — Full constitution
- [`AGENTS.md`](AGENTS.md) — Cross-tool instructions
- [`VIOLATIONS.md`](VIOLATIONS.md) — Behavioral lessons
- Scheduled agents: [`agents/morning-briefing.md`](agents/morning-briefing.md), [`agents/memory-consolidation.md`](agents/memory-consolidation.md)

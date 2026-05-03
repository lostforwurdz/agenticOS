# AgenticOS

A proactive agentic operating system built on Claude Code. Maintains memory across sessions, integrates with external tools, runs autonomous scheduled agents, and governs itself via the Constitution at [`CLAUDE.md`](CLAUDE.md).

## Layout

| Path | Contents |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Constitution — Claude-specific guidance, integrations, scheduled agents |
| [`AGENTS.md`](AGENTS.md) | Cross-tool universal instructions (read by Codex, Copilot, Gemini CLI, Aider) |
| [`VIOLATIONS.md`](VIOLATIONS.md) | Behavioral lessons logged after corrections |
| [`agents/`](agents/) | Active specialist subagent definitions (curated; archived ones in `agents/archived/` are preserved but not loaded) |
| [`skills/`](skills/) | Reusable skill definitions |
| [`workflows/`](workflows/) | Multi-step workflow definitions |
| [`gemini/skills/`](gemini/skills/) | Skills consumed by `agent-pool` MCP for Gemini CLI workers |
| [`scripts/`](scripts/) | Install + verification scripts (Linux + Windows) |

## Install on a new machine

```bash
git clone https://github.com/lostforwurdz/agenticOS.git ~/agenticOS
```

### Linux

```bash
~/agenticOS/scripts/install-linux.sh
```

Idempotent. Replaces existing symlinks; backs up real files to `~/.claude/_pre-symlink-backup-<timestamp>/`.

### Windows

**One-time prerequisite:** enable Developer Mode (Settings → Privacy & security → For developers → Developer Mode = ON) so symlinks can be created without admin elevation.

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\agenticOS\scripts\install-windows.ps1"
```

Idempotent. Same backup behavior as the Linux script.

### Verify hooks (any platform with bash + python3)

```bash
~/agenticOS/scripts/verify-hooks.sh
```

Static check that `~/.claude/settings.json` has the expected hooks wired and their dependencies (agent files, `bd prime` command) all resolve. Prints next-session live-test instructions at the end.

## Source of truth

The repository is the source of truth. Edits made to `~/.claude/CLAUDE.md` (etc.) modify the linked files inside this repo. Commit and push from `~/agenticOS/`.

The Linux and Windows installs both use symlinks pointing into the repo, so the workflow is identical on both machines: edit anywhere, commit + push from the repo, `git pull` on the other side.

## Beads memory and issues

Beads (`bd`) issue tracking and persistent memory are stored at `~/.beads/` and pushed via `bd dolt push` to a Dolt remote — separate from this repo. Sync independently:

```bash
bd dolt push   # at session close
bd dolt pull   # at session start on a different machine
```

The `vps-sync` agent automates the cross-machine pull workflow.

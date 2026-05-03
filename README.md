# AgenticOS

A proactive agentic operating system built on Claude Code. Maintains memory across sessions, integrates with external tools, runs autonomous scheduled agents, and governs itself via the Constitution at [`CLAUDE.md`](CLAUDE.md).

## Layout

| Path | Contents |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Constitution — Claude-specific guidance, integrations, scheduled agents |
| [`AGENTS.md`](AGENTS.md) | Cross-tool universal instructions (read by Codex, Copilot, Gemini CLI, Aider) |
| [`VIOLATIONS.md`](VIOLATIONS.md) | Behavioral lessons logged after corrections |
| [`agents/`](agents/) | 129 specialist subagent definitions |
| [`skills/`](skills/) | 26 reusable skill definitions |
| [`workflows/`](workflows/) | 12 multi-step workflow definitions |
| [`gemini/skills/`](gemini/skills/) | Skills consumed by `agent-pool` MCP for Gemini CLI workers |

## Install on a new machine

```bash
git clone https://github.com/lostforwurdz/agenticOS.git ~/agenticOS

# Symlink the AgenticOS content into the locations Claude Code expects.
ln -sf ~/agenticOS/CLAUDE.md     ~/.claude/CLAUDE.md
ln -sf ~/agenticOS/AGENTS.md     ~/.claude/AGENTS.md
ln -sf ~/agenticOS/VIOLATIONS.md ~/.claude/VIOLATIONS.md
ln -sf ~/agenticOS/agents        ~/.claude/agents
ln -sf ~/agenticOS/skills        ~/.claude/skills
ln -sf ~/agenticOS/workflows     ~/.claude/workflows
mkdir -p ~/.gemini
ln -sf ~/agenticOS/gemini/skills ~/.gemini/skills
```

## Source of truth

The repository is the source of truth. Edits made to `~/.claude/CLAUDE.md` (etc.) modify the linked files inside this repo. Commit and push from `~/agenticOS/`.

Beads (`bd`) issue tracking and persistent memory are stored separately at `~/.beads/` and pushed via `bd dolt push` to a Dolt remote — not in this repo.

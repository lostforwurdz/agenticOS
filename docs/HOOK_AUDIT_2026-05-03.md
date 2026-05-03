# Hook Audit — 2026-05-03

Audit of `~/.claude/settings.json` `hooks` block for orphan references.
Read-only: `settings.json` was not modified.

## Summary

- Total hook entries: **2**
- Hook events configured: `PreToolUse`, `SessionStart`
- Path references: **0** (0 broken)
- Agent references: **1** (0 broken)
- Command references: **1** (0 not on PATH)

## Hook inventory

| Event | Matcher | Type | Target |
|-------|---------|------|--------|
| `PreToolUse` | `EnterPlanMode` | `agent` | `violations-enforcer` |
| `SessionStart` | `""` (any) | `command` | `bd prime` |

## Findings

### Broken path references
None. The hooks block contains no path-like strings (no values starting with `/` or `~`).

### Missing agent references
None.

- `violations-enforcer` resolves to `/home/kobramaz/agenticOS/agents/violations-enforcer.md` (exists).

### Commands not on PATH
None.

- `bd prime` — first token `bd` resolves to `/home/kobramaz/.nvm/versions/node/v24.14.1/bin/bd` (on PATH).

## Recommendations

No action required. All hook references are intact:

1. The `PreToolUse:EnterPlanMode` agent hook fires `violations-enforcer.md`, which is present in the agents directory.
2. The `SessionStart` command hook runs `bd prime`, and the `bd` binary is installed via the active nvm node 24.14.1 toolchain.

### Forward-looking notes (not action items)

- `bd` lives under nvm — if the user changes node versions or removes that nvm install, the `SessionStart` hook will silently fail. Consider symlinking `bd` into a stable location (e.g. `~/.local/bin`) or installing it globally outside of nvm if that risk matters.
- Only 2 hooks are configured. The earlier inspection mentioned in the task brief is accurate — there are no surprise/undocumented hook entries.

## Methodology

```bash
jq '.hooks // {}' ~/.claude/settings.json > /tmp/hooks-config.json
jq -r '.. | strings | select(startswith("/") or startswith("~"))' /tmp/hooks-config.json | sort -u > /tmp/hook-paths.txt
jq -r '.. | objects | select(.type? == "agent") | .agent' /tmp/hooks-config.json | sort -u > /tmp/hook-agents.txt
jq -r '.. | objects | select(.type? == "command") | .command' /tmp/hooks-config.json | sort -u > /tmp/hook-commands.txt
```

Each agent name was checked against `~/agenticOS/agents/<name>.md`; each command's first token was checked with `command -v`.

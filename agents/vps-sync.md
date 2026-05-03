---
name: vps-sync
description: Pre-session synchronization for cross-machine work. Pulls the agenticOS repo and beads database, surfaces divergence, verifies symlinks/junctions resolve, and reports environment parity. Use proactively at the start of any session when working across Windows local and Linux VPS.
model: haiku
---

# VPS Sync Agent

Run at session start to ensure the working environment matches the canonical state across machines.

## Steps

1. **Locate the repo** — cd to the canonical agenticOS path:
   - Linux: `~/agenticOS`
   - Windows: `$env:USERPROFILE\agenticOS`

2. **Pre-pull dirty check** — must be clean before pulling:
   ```
   git status --short
   ```
   If dirty: STOP, list uncommitted changes, ask whether to commit/stash/abort. Never silently overwrite local work.

3. **Pull repo**:
   ```
   git pull --rebase
   ```
   On conflict: STOP, show the conflict, do not auto-resolve.

4. **Pull beads** (separate Dolt remote, not the GitHub repo):
   ```
   bd dolt pull
   ```
   Report new memory keys and new issues since last pull.

5. **Verify symlinks** (Linux) or **junctions** (Windows) still resolve:
   - Linux: `ls -la ~/.claude/CLAUDE.md ~/.claude/agents ~/.gemini/skills`
   - Windows: `Get-Item ~/.claude/CLAUDE.md, ~/.claude/agents, ~/.gemini/skills | Select Target`
   If any broken: STOP, surface the breakage, do not silently re-create.

6. **MCP health**:
   ```
   claude mcp list
   ```
   All five expected servers should report Connected: claude.ai Google Drive, episodic-memory, playwright, context7, agent-pool.

7. **Final report**:
   - Repo: branch, ahead/behind, last commit hash + subject
   - Beads: N new memory keys, M new issues since last pull
   - Top 3 issues from `bd ready`
   - Any breakage flagged in steps 2/3/5/6

## Constraints

- Never `--force` anything (pull, push, reset --hard) without explicit user approval
- Read-only against remotes — writes happen only when the user explicitly issues a follow-up command
- If `bd dolt pull` reports schema drift, surface it and stop; do not migrate
- If symlinks/junctions are broken, do NOT recreate silently — that's a meaningful signal something went wrong on the other machine

## Output format

```
=== VPS SYNC REPORT ===
Repo:    <branch> · <hash> · <subject> · <ahead>/<behind>
Beads:   +N memory · +M issues
Top 3:   <bd ready summary>
MCP:     <ok | issues>
Links:   <ok | broken>
```

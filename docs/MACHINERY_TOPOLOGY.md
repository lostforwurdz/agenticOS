## Topology: SYMLINKED

**Summary:** `~/.claude/` and `~/agenticOS/` are NOT independent copies — the machinery directories under `~/.claude/` are symlinks pointing INTO `~/agenticOS/`, which is the canonical physical location. Specifically, `~/.claude/agents`, `~/.claude/skills`, `~/.claude/workflows` are symlinks resolving to `/home/kobramaz/agenticOS/agents`, `/skills`, `/workflows` respectively. The top-level files `~/.claude/CLAUDE.md`, `~/.claude/AGENTS.md`, and `~/.claude/VIOLATIONS.md` are also symlinks into `~/agenticOS/`. Therefore the agenticOS rewrite agent's assertion ("This repository is the canonical source. Edits to ~/.claude/CLAUDE.md modify symlinked files here") is VERIFIED for these paths. Anomaly: `~/.claude/commands` does NOT exist (neither file, directory, nor symlink — `readlink -f` echoed the path back because the target is missing); confirmed via `test -e` and `test -L`. Direction: `~/.claude/{agents,skills,workflows,CLAUDE.md,AGENTS.md,VIOLATIONS.md}` → `~/agenticOS/...`. **Canonical edits should target `~/agenticOS/`** and be committed to the agenticOS git repo for cross-machine propagation.

---

total 664
drwxrwxr-x  23 kobramaz kobramaz   4096 May  3 12:31 .
drwx--x--x  47 kobramaz kobramaz   4096 May  3 14:30 ..
lrwxrwxrwx   1 kobramaz kobramaz     31 May  2 22:41 agents -> /home/kobramaz/agenticOS/agents
lrwxrwxrwx   1 kobramaz kobramaz     34 May  2 22:41 AGENTS.md -> /home/kobramaz/agenticOS/AGENTS.md
drwxrwxr-x   2 kobramaz kobramaz   4096 May  3 12:15 audits
drwxrwxr-x   2 kobramaz kobramaz   4096 May  3 14:30 backups
drwxrwxr-x   3 kobramaz kobramaz   4096 Apr 25 23:25 .beads
drwxrwxr-x   2 kobramaz kobramaz   4096 Apr  8 22:57 cache
lrwxrwxrwx   1 kobramaz kobramaz     34 May  2 22:41 CLAUDE.md -> /home/kobramaz/agenticOS/CLAUDE.md
-rw-------   1 kobramaz kobramaz    528 May  3 09:52 .credentials.json
drwxrwxr-x   2 kobramaz kobramaz  20480 May  2 01:19 debug
drwxrwxr-x   2 kobramaz kobramaz   4096 Apr  8 22:57 downloads
drwxrwxr-x  34 kobramaz kobramaz   4096 May  2 22:07 file-history
-rw-rw-r--   1 kobramaz kobramaz    117 Apr 25 23:25 .gitignore
-rw-------   1 kobramaz kobramaz 113617 Apr 16 16:29 history.jsonl
drwxrwxr-x   2 kobramaz kobramaz   4096 Apr 16 17:50 hooks
drwx------   2 kobramaz kobramaz   4096 May  2 15:29 ide
-rw-rw-r--   1 kobramaz kobramaz      2 Apr 26 19:19 mcp-needs-auth-cache.json
drwxrwxr-x   2 kobramaz kobramaz   4096 May  2 22:05 mcp-servers
drwxrwxr-x   2 kobramaz kobramaz   4096 Apr 12 17:15 paste-cache
drwxrwxr-x   5 kobramaz kobramaz   4096 Apr 16 16:33 plugins
drwxrwxr-x   6 kobramaz kobramaz   4096 May  2 22:40 _pre-symlink-backup-2026-05-02
drwxrwxr-x  11 kobramaz kobramaz   4096 Apr 30 21:01 projects
drwxrwxr-x 391 kobramaz kobramaz  32768 May  3 04:06 session-env
drwx------   2 kobramaz kobramaz   4096 May  3 04:07 sessions
-rw-rw-r--   1 kobramaz kobramaz  73875 May  3 12:31 settings.json
-rw-rw-r--   1 kobramaz kobramaz  63133 Apr 30 20:52 settings.json.bak-20260430-205212
-rw-rw-r--   1 kobramaz kobramaz  69725 May  2 22:05 settings.json.bak-pre-agentpool
-rw-rw-r--   1 kobramaz kobramaz  71982 May  3 11:35 settings.json.bak-pre-hooks-wire
-rw-rw-r--   1 kobramaz kobramaz  72214 May  3 11:40 settings.json.bak-pre-sessionstart-hook
drwxrwxr-x   2 kobramaz kobramaz   4096 May  3 12:12 shell-snapshots
lrwxrwxrwx   1 kobramaz kobramaz     31 May  2 22:41 skills -> /home/kobramaz/agenticOS/skills
-rw-------   1 kobramaz kobramaz   4094 May  2 01:19 stats-cache.json
drwxrwxr-x   2 kobramaz kobramaz   4096 Apr 30 21:13 statsig
drwxrwxr-x   4 kobramaz kobramaz   4096 Apr 12 02:09 tasks
drwxrwxr-x   2 kobramaz kobramaz   4096 Apr 29 22:47 telemetry
drwxrwxr-x   2 kobramaz kobramaz  32768 May  2 01:19 todos
lrwxrwxrwx   1 kobramaz kobramaz     38 May  2 22:41 VIOLATIONS.md -> /home/kobramaz/agenticOS/VIOLATIONS.md
lrwxrwxrwx   1 kobramaz kobramaz     34 May  2 22:41 workflows -> /home/kobramaz/agenticOS/workflows
---
total 72
drwxrwxr-x  8 kobramaz kobramaz 4096 May  3 12:33 .
drwx--x--x 47 kobramaz kobramaz 4096 May  3 14:30 ..
drwxrwxr-x  3 kobramaz kobramaz 4096 May  3 11:40 agents
-rw-rw-r--  1 kobramaz kobramaz 3195 May  2 22:39 AGENTS.md
-rw-rw-r--  1 kobramaz kobramaz 7656 May  3 12:32 CLAUDE.md
-rw-rw-r--  1 kobramaz kobramaz  359 May  3 12:33 DELETION_LOG.md
drwxrwxr-x  3 kobramaz kobramaz 4096 May  2 22:39 gemini
drwxrwxr-x  8 kobramaz kobramaz 4096 May  3 13:58 .git
-rw-rw-r--  1 kobramaz kobramaz  516 May  2 22:39 .gitignore
-rw-rw-r--  1 kobramaz kobramaz 8537 May  3 12:33 README.md
-rw-rw-r--  1 kobramaz kobramaz 3597 May  3 12:33 REWRITE_LOG.md
drwxrwxr-x  2 kobramaz kobramaz 4096 May  3 12:10 scripts
drwxrwxr-x  8 kobramaz kobramaz 4096 May  3 11:24 skills
-rw-rw-r--  1 kobramaz kobramaz 1795 May  2 22:39 VIOLATIONS.md
drwxrwxr-x  3 kobramaz kobramaz 4096 May  3 11:21 workflows
/home/kobramaz/.claude/agents -> /home/kobramaz/agenticOS/agents
/home/kobramaz/.claude/skills -> /home/kobramaz/agenticOS/skills
/home/kobramaz/.claude/workflows -> /home/kobramaz/agenticOS/workflows
/home/kobramaz/.claude/commands -> /home/kobramaz/.claude/commands
/home/kobramaz/agenticOS/agents -> /home/kobramaz/agenticOS/agents
/home/kobramaz/agenticOS/skills -> /home/kobramaz/agenticOS/skills
/home/kobramaz/agenticOS/workflows -> /home/kobramaz/agenticOS/workflows

---

## Anomaly notes

- `~/.claude/commands`: does NOT exist. `readlink -f` echoed the path back because the path is missing (a quirk of `readlink -f`, which still produces output when nothing exists at the target). Verified: `ls -la` returned "No such file or directory"; `test -e` returned false; `test -L` returned false.
- `~/agenticOS/agents`, `~/agenticOS/skills`, `~/agenticOS/workflows` resolve to themselves (they are real directories, not symlinks). This confirms agenticOS is the canonical physical location.
- `~/.claude/_pre-symlink-backup-2026-05-02/` exists, indicating the symlink topology was set up on 2026-05-02 and the previous canonical content was preserved as a backup. The symlinks themselves are dated `May  2 22:41`, consistent with a single migration event.

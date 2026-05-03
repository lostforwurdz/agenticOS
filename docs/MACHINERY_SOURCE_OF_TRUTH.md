# Machinery Source of Truth

**Last updated:** 2026-05-03
**Topology source:** [`MACHINERY_TOPOLOGY.md`](./MACHINERY_TOPOLOGY.md) (Task 1)
**Inventory source:** [`MACHINERY_INVENTORY_CANONICAL.json`](./MACHINERY_INVENTORY_CANONICAL.json), [`MACHINERY_INVENTORY_PROJECTS.json`](./MACHINERY_INVENTORY_PROJECTS.json) (Tasks 2, 3)

This document defines where each piece of Claude Code machinery actually lives, how to edit it safely, and how to resolve drift between the canonical root and project tips. It is the reference for Tasks 5-14 of the machinery audit.

---

## Topology summary (verified 2026-05-03)

`~/.claude/` is the **harness root** Claude Code reads at runtime. `~/agenticOS/` is the **canonical physical location** and the git repo. The machinery directories under `~/.claude/` are symlinks pointing into `~/agenticOS/`:

```
~/.claude/agents       -> ~/agenticOS/agents       (symlink)
~/.claude/skills       -> ~/agenticOS/skills       (symlink)
~/.claude/workflows    -> ~/agenticOS/workflows    (symlink)
~/.claude/CLAUDE.md    -> ~/agenticOS/CLAUDE.md    (symlink)
~/.claude/AGENTS.md    -> ~/agenticOS/AGENTS.md    (symlink)
~/.claude/VIOLATIONS.md -> ~/agenticOS/VIOLATIONS.md (symlink)
```

`~/.claude/commands/` does **not** exist (neither file, dir, nor symlink). Do not create it without an explicit reason.

`~/.claude/{settings.json, hooks/, mcp-servers/, plugins/}` are **not** symlinked — they are real files/dirs under `~/.claude/` only.

---

## Canonical paths

| File type | Canonical path (where to edit) | Symlinked? | Notes |
|---|---|---|---|
| Agent | `~/agenticOS/agents/<name>.md` | Yes (`~/.claude/agents` -> here) | Editing `~/.claude/agents/<name>.md` modifies the same file. Prefer the agenticOS path for clarity. |
| Skill (single-file) | `~/agenticOS/skills/<name>.md` | Yes | 21 top-level skill markdown files. Used when no resources are needed. |
| Skill (directory) | `~/agenticOS/skills/<name>/SKILL.md` | Yes | 6 skill directories with resources/sub-files. Use when the skill has support files. |
| Workflow | `~/agenticOS/workflows/<name>.md` | Yes | Reference documents; not auto-loaded. Invoked via `/<name>` slash command or referenced from CLAUDE.md. |
| Constitution | `~/agenticOS/CLAUDE.md` | Yes | Global instructions. Top of every session. |
| Agent index | `~/agenticOS/AGENTS.md` | Yes | Human-readable agent roster. Update when adding/removing agents. |
| Violations log | `~/agenticOS/VIOLATIONS.md` | Yes | Append-only record of constitution breaches. |
| Settings | `~/.claude/settings.json` | No | Real file. Hooks, permissions, env vars. Edit via `update-config` skill. |
| Hooks (scripts) | `~/.claude/hooks/<name>/` | No | Real dir. Shell/Python scripts invoked by `settings.json` hooks. |
| MCP servers | `~/.claude/mcp-servers/` | No | Real dir. MCP server configs. |
| Plugins | `~/.claude/plugins/` | No | Managed by `/mcp` and plugin install commands. |
| Project tip (per-project) | `~/Documents/<project>/.claude/{agents,skills,workflows}/` | No | Project-local overrides; see "Project tip rules" below. |

---

## Edit flow

**For symlinked files (agents, skills, workflows, CLAUDE.md, AGENTS.md, VIOLATIONS.md):**

1. Edit at the agenticOS path: `~/agenticOS/<area>/<file>.md`. Editing via `~/.claude/<area>/<file>.md` modifies the same physical file (it is a symlink), but the agenticOS path makes the canonical relationship explicit.
2. Test in the current session.
3. Commit + push from `~/agenticOS`:
   ```bash
   cd ~/agenticOS && git add <path> && git commit -m "..." && git push
   ```
4. (Optional) Propagate to a project tip if the change is project-relevant. See "Project tip rules".

**For non-symlinked files (settings.json, hooks/, mcp-servers/):**

1. Edit at `~/.claude/<path>` directly. There is no agenticOS mirror.
2. For `settings.json` specifically, prefer the `update-config` skill — it preserves structure and validates JSON.
3. Back up before editing: `cp settings.json settings.json.bak-$(date +%Y%m%d-%H%M%S)`. Several `.bak-*` files already exist in `~/.claude/` for prior edits.
4. These files are **not** in the agenticOS git repo and do not propagate across machines automatically.

**Critical:** `~/.claude/agents/coder.md` and `~/agenticOS/agents/coder.md` are the **same file** (one symlink). Do not "sync" between them — they cannot drift. Use either path; the agenticOS path is preferred for clarity.

---

## Project tip rules

A project tip is `~/Documents/<project>/.claude/`. Tips contain project-specific overrides. They are **separate copies**, not symlinks — they CAN drift.

Per Task 3 inventory (2026-05-03):
- `atbfuture` (99 files) and `antigravity` (39 files) have substantive project tips.
- `CMS_Next`, `hrhh`, `project_next_zach` have only `settings.local.json` (no machinery overrides).
- `neighborhood_authority` and `wiki-compiler` have no `.claude/` directory.

### Resolution rules

| Case | Diagnosis | Action |
|---|---|---|
| Project file is **byte-identical** to canonical | Stale exact copy | Delete from project. Project will fall back to root automatically. |
| Project file **differs** from canonical, change is intentional override | Legitimate drift | Keep. Add a comment header noting why this differs. Document in project's local CLAUDE.md if non-obvious. |
| Project file **differs** from canonical, change is unintentional drift | Bad drift | Re-sync from canonical (`cp ~/agenticOS/<path> ~/Documents/<project>/.claude/<path>`). |
| Project file is **better** than canonical (improvements made locally) | Upstream improvement | Promote: copy to `~/agenticOS/<area>/<file>`, commit, then delete from project (now stale-equal). |
| Project file has **no canonical counterpart** | Orphan | Decide: (a) promote to canonical if useful elsewhere; (b) keep project-local if genuinely project-specific; (c) delete if obsolete. |

### Exact-copy delete rule

If `sha256sum ~/agenticOS/<path>` equals `sha256sum ~/Documents/<project>/.claude/<path>`, the project file adds nothing. Delete it. Project tips should only contain files that differ from canonical.

---

## Frontmatter requirements

YAML frontmatter (`---\nkey: value\n---`) at the very top of the file. Per type:

| Type | Required fields | Optional fields |
|---|---|---|
| Agent | `name`, `description`, `model` | `tools` (default: all), `color` |
| Skill (single-file or `SKILL.md`) | `name`, `description` | `allowed-tools`, `last_updated`, `path`, `dependencies` |
| Workflow | `description` | `name`, `allowed-tools` |
| CLAUDE.md / AGENTS.md / VIOLATIONS.md | None | None — these are not loaded by name |

### Field rules

- `name`: must match the filename stem (`coder.md` -> `name: coder`). Kebab-case.
- `description`: one sentence, terse, present-tense. Describes what the entity does, not how. No marketing language.
- `model`: `sonnet` for utility/dispatch agents, `opus` for complex review/architecture agents. Required for agents.
- `last_updated`: ISO date (`YYYY-MM-DD`). Optional but recommended for skills.

### Detected gaps (Task 2)

- 8 active top-level skill files lack frontmatter. Task 5 will fix.
- 0 known frontmatter gaps in agents (verify in Task 5).

---

## Naming conventions

**Rule: kebab-case only. No underscores. No capital letters. No spaces.**

| Good | Bad |
|---|---|
| `security-auditor.md` | `Security_Auditor.md`, `securityAuditor.md`, `security_auditor.md` |
| `code-review.md` | `code_review.md`, `CodeReview.md` |
| `pre-commit.md` | `pre_commit.md`, `Pre-Commit.md` |
| `nextjs-developer.md` | `nextjs_developer.md`, `NextJSDeveloper.md` |

**Filename = name in frontmatter.** `coder.md` has `name: coder`. They must match exactly.

**Skill directories:** the directory name is the skill name. `~/agenticOS/skills/codeql/SKILL.md` defines the `codeql` skill — the inner file is always literally `SKILL.md`.

**Cross-references:** when one file references another agent/skill/workflow, use the kebab-case name in backticks: `` `code-review` ``, not `` `Code Review` `` or `` `code_review` ``.

---

## Common mistakes to avoid

1. **Creating parallel copies.** Do not `cp ~/agenticOS/agents/coder.md ~/.claude/agents/coder.md`. The latter is a symlink resolving to the former — the copy will overwrite the canonical and break the symlink direction perception.
2. **Editing through `_pre-symlink-backup-2026-05-02/`.** That directory is the pre-migration archive. Read-only reference. Do not edit.
3. **Putting hooks scripts in `~/agenticOS/`.** `~/.claude/hooks/` is not symlinked. Hook scripts must live under `~/.claude/hooks/` and be referenced absolutely from `settings.json`.
4. **Adding files to `~/.claude/commands/`.** That directory does not exist. Slash commands are defined by skills and workflows, not a `commands/` folder.
5. **Forgetting to commit.** `~/agenticOS/` is a git repo; `~/.claude/` is not. Edits via the `~/.claude/` symlink path still need a `git -C ~/agenticOS commit && git push`.
6. **Drift in project tips that should be exact copies.** If a project tip has the same content as canonical, delete it. Tips should only carry overrides.

---

## Quick reference

```bash
# Edit canonical agent
$EDITOR ~/agenticOS/agents/coder.md

# Edit canonical skill (single-file)
$EDITOR ~/agenticOS/skills/code-review.md

# Edit canonical skill (directory)
$EDITOR ~/agenticOS/skills/codeql/SKILL.md

# Edit settings (NOT symlinked, not in git)
$EDITOR ~/.claude/settings.json

# Verify a file is the canonical (symlinked) one
readlink -f ~/.claude/agents/coder.md
# should print: /home/kobramaz/agenticOS/agents/coder.md

# Compare project tip to canonical
diff ~/agenticOS/agents/coder.md ~/Documents/atbfuture/.claude/agents/coder.md

# Commit + push from canonical
cd ~/agenticOS && git add . && git commit -m "..." && git push
```

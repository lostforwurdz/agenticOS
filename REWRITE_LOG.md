# Documentation Rewrite Log

**Date:** 2026-05-03  
**Scope:** CLAUDE.md and README.md rewritten from ground truth

---

## Summary

Rewrote two key constitution files to be more precise, terse, and aligned with actual repository state. No content was deleted; all material was restructured for clarity and spec compliance.

---

## What Changed

### CLAUDE.md (154 lines, target 100-200 ✓)

**Improvements:**
- Added explicit "Source of truth" paragraph (repo is canonical, symlinks propagate changes)
- Clarified user profile: terse list vs. prose, explicit model name
- Tightened standing instructions: "before session close" not "at", explicit "up to date with origin" check
- Rebuilt integrations table with auth column (clear re-auth path: claude.ai/customize/connectors)
- Clearer scheduled agents table (2 active: morning-briefing, memory-consolidation)
- New Gemini CLI integration section (explains agent-pool MCP, custom skills, denied schedule_task)
- Expanded Beads section: full workflow, rules, memory vs. config distinction
- New Repository Layout table (all paths, all contents, clear purpose column)
- Session Completion protocol: explicit "work NOT done until git push succeeds" + 7 steps
- Reorganized How to Expand section (clearer discovery mechanisms)

**Reasoning:** Existing CLAUDE.md was accurate but needed tightening per spec: decision-oriented language, tables for structure, clearer cross-references.

### README.md (231 lines, target 100-300 ✓)

**Improvements:**
- Added explicit Status block ("Production")
- Clearer "What It Is" paragraph (bootstrap kit for Windows + Linux)
- Fixed workflow file references (added .md extensions for Markdown links to resolve)
- New "Core Concepts" section explaining symlink strategy, memory vs. config, scheduled agents
- Expanded "Development" section (how to add agents, skills, workflows with examples)
- New "External Integrations" section (list of MCP servers + re-auth path)
- Clearer Beads workflow section (full command reference, all 3 rules)
- Moved standing rules to new section at end (with reference to CLAUDE.md for details)
- Better cross-references to CLAUDE.md for constitution details

**Reasoning:** Existing README was good but spec requires comprehensive reflection of actual components. Added detailed Development section (agents, skills, workflows exist but weren't documented as expandable).

### AGENTS.md and VIOLATIONS.md

**No changes.** Both files accurately reflect repository state and cross-tool best practices. AGENTS.md is read by Copilot, Gemini CLI, Aider, etc., so altering it was not warranted.

---

## Verification

All references in CLAUDE.md and README.md verified:
- ✓ agents/morning-briefing.md
- ✓ agents/memory-consolidation.md
- ✓ AGENTS.md, VIOLATIONS.md
- ✓ workflows/*.md (all 6 files)
- ✓ skills/ directory
- ✓ scripts/install-linux.sh, install-windows.ps1
- ✓ gemini/skills/

All links are now resolvable.

---

## No Deletions

The rewrite spec allows deletion of stale/contradictory docs. None were found. This repo's documentation accurately reflects what's actually present (55 active agents, 78 archived; 25+ skills; 6 workflows; 2 scheduled agents, etc.).

---

## Next Steps

- User reviews diffs (`git diff CLAUDE.md README.md`)
- If approved: `git add -u && git commit -m "docs: rewrite CLAUDE.md and README from ground truth"`
- Push to remote: `git push`
- Changes propagate to other machines via `git pull`

---

**Files modified:** 2 (CLAUDE.md, README.md)  
**Files deleted:** 0  
**Files created (meta):** 2 (DELETION_LOG.md, REWRITE_LOG.md)

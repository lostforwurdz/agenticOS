---
description: Run at the end of every session. Work is NOT complete until git push succeeds.
---

# /session-close - Session Close

Local commits without a push strand work on one machine. bd issues closed without a `bd remember` entry lose the non-obvious decisions that future sessions need to avoid re-solving the same problems. This protocol prevents both: every session ends with memory persisted, issues updated, and all changes pushed to origin.

## When To Use

- User signals end of session ("we're done", "wrap up", "closing").
- Before closing a laptop or switching machines (Windows ↔ Linux VPS).
- Before a long break where the next session will start cold.
- After completing a significant milestone even mid-session (to ensure a clean checkpoint).

## Workflow

### Phase 1: File follow-ups

1. Review the work done during this session. For any remaining work, open tasks, or uncovered follow-up items, run `BEADS_DIR=~/.beads bd create` to file a bd issue. Do not leave follow-up items as mental notes or inline comments.
2. Ensure every issue filed has a meaningful title and enough description that a future session can act on it without re-reading this session's transcript.

### Phase 2: Quality gates

1. If any code changed during this session, run the repo-appropriate gate sequence. Do not skip.
   - JavaScript/TypeScript projects: `pnpm lint && pnpm test && pnpm build` (or repo equivalent).
   - Python projects: `pytest` (or repo equivalent) + linter.
   - Other repos: check `package.json`, `Makefile`, or CI config for the canonical gate commands.
2. If gates fail, fix before proceeding. Do not push failing code.
3. If no code changed (docs-only, memory-only session), state this explicitly and skip to Phase 3.

### Phase 3: Update issue status

1. Run `BEADS_DIR=~/.beads bd close <id>` for every issue completed during this session.
2. Run `BEADS_DIR=~/.beads bd update <id>` for any in-progress issues that need updated notes (e.g., what was done, what remains, what blocked you).
3. Do not leave finished work as open issues — stale open issues pollute the ready queue.

### Phase 4: Persist non-obvious decisions

1. For every non-obvious decision made during this session — architectural choices, gotchas discovered, workarounds applied, external dependencies learned — run:
   ```bash
   BEADS_DIR=~/.beads bd remember --key "<type>.<slug>" "<decision or finding>"
   ```
2. Types: `arch`, `gotcha`, `decision`, `convention`, `feedback`, `session`, `blocker`.
3. Do not save what is already obvious from the code or git history. Save what future-you would need that isn't there.
4. See `CLAUDE.md` "Memory hygiene" standing instruction for the full rule.

### Phase 4.4: Decisions sync

1. Dispatch the `decisions-sync` agent (`agents/decisions-sync.md`) against the current session's chat transcript at `~/.claude/projects/<slugified-cwd>/<session-uuid>.jsonl`.
2. The agent identifies user decisions (selections, standing rules, constraints, approvals, sequencing choices, scope cuts, preferences), captures each as WHAT + WHY + WHEN + WHERE + verbatim QUOTE, dedupes against existing `decision.*` bd entries, and writes new entries via `bd remember --key "decision.<YYYY-MM-DD>.<slug>" "..."`.
3. Future code-change sessions can then `bd memories <keyword>` to find "why did we choose X" with full reasoning + audit trail.
4. The agent uses an independent reviewer subagent to verify quotes are verbatim and WHY is grounded in the source turn before any bd write.
5. If the chat log has no captureable decisions, agent exits cleanly with "no decisions identified."

### Phase 4.5: Documentation sync

1. Dispatch the `docs-sync` agent (`agents/docs-sync.md`) against this session's commit range. Default: `git log origin/main..HEAD`.
2. The agent identifies docs that drifted because of source changes (README, ARCHITECTURE.md, CLAUDE.md, docs/*, AGENTS.md, workflows/*, agents/*, loom-openapi.json), applies precise edits, then runs an independent reviewer subagent on the doc diff before committing.
3. On reviewer approval: a `docs: sync from <range>` commit appears. Proceed to Phase 5.
4. On reviewer rejection or unresolved drift: the agent writes findings to `.claude/audits/AUDIT_DOCS_SYNC_<YYYY-MM-DD>.md` and files bd issues for items it could not fix. Review and act on those before pushing OR file as session-out follow-up before continuing — do NOT skip the push if drift remains, but do NOT bury silently either.
5. If the range is empty or contains only doc-only commits: agent exits cleanly with "no drift detected." State this explicitly and proceed.
6. The docs commit goes through the same reviewer gate as code commits (user standing rule — no exceptions).

### Phase 5: Push

1. Run the mandatory push sequence in order — do not reorder or skip steps:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   ```
2. If `git pull --rebase` produces conflicts, resolve them before proceeding. Do not `git push` with unresolved conflicts.
3. `bd dolt push` syncs beads memory to the Dolt remote. Without this, memory diverges across machines.

### Phase 6: Verify

1. Run `git status`. It MUST show "Your branch is up to date with 'origin/<branch>'". If it does not, diagnose and re-push.
2. Run `git log --oneline -3` to confirm the expected commits are present on the remote.
3. If anything is missing, do not declare done — fix and re-verify.

### Phase 7: Hand off

1. If the next session will need context that isn't already in bd issues or persisted memories, save a session summary:
   ```bash
   BEADS_DIR=~/.beads bd remember --key "session.<YYYY-MM-DD>" "<what was done, what's next, key context>"
   ```
2. Leave the repo in a state where a cold-start session running `workflows/session-start.md` can pick up without reading this session's transcript.

## Quality Guidelines

> [!CAUTION]
> **BLOCKING STEP.** Work is NOT complete until `git status` shows "Your branch is up to date with 'origin/<branch>'". Never declare done before pushing. Stopping early strands work locally and risks losing it on machine failure or multi-machine divergence.

- MUST: every session that changed code ends with a green push. No exceptions.
- MUST NOT: skip `bd dolt push`. Beads memory diverges across machines without it — the next session on a different machine starts without this session's knowledge.
- MUST NOT: push failing tests or broken builds. Fix quality gates first.
- SHOULD: clear stashes (`git stash list` — drop any stale stashes).
- SHOULD: prune merged remote branches (`git fetch --prune`).
- SHOULD: `bd close` every completed issue before pushing — the commit hash is available in `git log` for reference in the issue.

## References

- `CLAUDE.md` — `## Standing Instructions` #5 ("Session close mandatory") and #1 ("Memory hygiene")
- `workflows/code-writing.md` — run this during the session before reaching close; quality gates here are the tail of that workflow
- `CLAUDE.md` — `## Beads Memory and Issue Tracking` for full bd command reference

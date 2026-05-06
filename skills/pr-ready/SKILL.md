---
name: pr-ready
description: >-
  Sequential pre-merge gate composite. Runs pre-commit workflow (parallel
  reviewer + tester), then conditionally dispatches security-gate or
  dual-review based on diff paths, then git-manager for PR creation.
  Invoke when ready to open a PR — replaces the manual sequence of
  pre-commit, security checks, and PR drafting with a single chain.
---

# PR Ready

Sequential composite gate for PR creation. Each phase blocks the next; a Critical finding halts the chain until resolved.

## Trigger

Invoke when user says "open PR", "ready to merge", or "create PR", or after `git push` when PR creation is the next step.

## Phase 1 — Pre-Commit Gate (sequential)

Invoke `workflows/pre-commit.md`. That workflow internally dispatches `reviewer` + `tester` in parallel.

> [!CAUTION]
> **BLOCKING STEP.** Wait for a Pass verdict before proceeding. Any Critical finding halts the chain — fix and re-run Phase 1.

## Phase 2 — Conditional Security Gate (sequential)

Wait for Phase 1. Run `git diff --name-only main...HEAD` and apply the first matching rule:

| Condition | Action |
|---|---|
| Diff touches `auth/`, `lib/auth`, `payment`, `encrypt`, `migrations/`, or `schema.ts` | Dispatch `dual-review` skill |
| Diff touches `api/`, `middleware/`, `secrets`, or `*.env*` | Dispatch `security-gate` skill |
| Neither | Skip — proceed to Phase 3 |

> [!CAUTION]
> **BLOCKING STEP.** If Phase 2 runs and returns any Critical finding, halt until resolved and Phase 2 is re-run.

## Phase 3 — PR Creation (sequential)

Wait for Phase 1 and Phase 2 (if triggered) to complete. Dispatch `git-manager` agent with the diff summary, branch name, and all gate reports. `git-manager` drafts the PR title and body and creates the PR. PR body must link all gate reports.

## Verification

- [ ] Phase 1 pre-commit gate returned Pass.
- [ ] Phase 2 ran and passed (or correctly skipped).
- [ ] PR URL returned from `git-manager`.
- [ ] All gate reports linked in PR body.

## References

- `workflows/pre-commit.md` — pre-commit workflow dispatched in Phase 1
- `skills/security-gate/SKILL.md` — auth/secrets parallel security fan-out
- `skills/dual-review/SKILL.md` — high-stakes parallel review for sensitive diffs
- `agents/git-manager.md` — PR drafting and creation agent

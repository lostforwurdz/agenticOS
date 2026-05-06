---
description: Full pre-release pipeline: audit → fix → verify → deploy-gate → PR. Nothing ships with P1 issues open.
---

# /release-prep - Release Prep

Confidence at release time requires more than passing tests. A deployment that skips the audit phase ships whatever bugs accumulated since the last review. A deployment that skips the deploy-gate ships into an environment that may not accept the build. This workflow closes both gaps: audit first, fix P1 blockers, verify the full suite, validate the deployment environment, then generate the release PR. Each gate is sequential and hard — if a gate fails, the pipeline stops.

## When To Use

- Before any production or staging release.
- After a sprint or significant feature merge.
- When prompted by the orchestrator after `full-audit` P1 count drops to 0.

## Workflow

### Phase 1: Full Audit (parallel)

Dispatch `workflows/full-audit.md`. Wait for `FIXES.md` to be written before proceeding.

This dispatches all 9 audit agents in parallel (see `full-audit.md` for the full agent table and output schema). Do not reproduce the agent list here — follow `full-audit.md` exactly.

**Gate:** `FIXES.md` exists and `debugger` has produced the P1–P4 summary.

### Phase 2: Fix Planning (sequential)

`debugger` has already written `.claude/audits/FIXES.md`. Orchestrator presents to user:

- P1 count (release blockers)
- P2 count (should fix)
- Estimated total effort

**Gate:** User reviews `FIXES.md` and explicitly approves proceeding to Phase 3. Do not auto-advance.

### Phase 3: Fix P1 Items (sequential, one at a time)

Dispatch `coder` for each P1 item in `FIXES.md`, one at a time:

1. Read the FIXES.md entry for the item
2. Implement minimal fix (no scope creep)
3. Run the verify command listed in the FIXES.md entry for that item (see `skills/AUDIT.md` for standard verify patterns)
4. Mark `[x]` in FIXES.md
5. Run the repo test suite per `workflows/code-writing.md` Phase 4 before starting the next fix

Follow `workflows/code-writing.md` at each fix boundary (reviewer gate before commit).

**Gate:** Zero P1 items remain unchecked in FIXES.md.

### Phase 4: Verification (parallel)

Dispatch `tester` and the `security-gate` skill in a single message:

| Agent / Skill | Scope |
|---------------|-------|
| `tester` | Full suite — tsc + lint + all tests. All must pass. |
| `security-gate` (`skills/security-gate/SKILL.md`) | Fans out semgrep + codeql + supply-chain-risk-auditor + insecure-defaults + security-auditor + differential-review in parallel; produces a consolidated SECURITY_GATE report |

**Gate:** 0 test failures + 0 Critical findings in the SECURITY_GATE report. A Critical finding halts the release — do not advance to Phase 5 until it is resolved.

### Phase 5: Deploy Validation (sequential)

Dispatch `deploy-checker` for full pre-deploy check:

- Build succeeds
- Environment variables valid and complete
- Dependency health clean (supply-chain-risk-auditor included)
- Deployment provider config (Vercel + Cloudflare per project context, or project-specific provider) validated
- Health endpoint responds instantly

**Gate:** Verdict must be PASS (not WARN). No exceptions for release.

### Phase 6: Release PR (sequential)

Dispatch `git-manager` to create the release PR:

1. Verify tests pass (should already be confirmed from Phase 4)
2. Write PR description including: summary of changes, FIXES.md items applied, test results, deploy checklist
3. Push branch and open PR

## Release Blockers

The release does not ship if any of these are true:

- [ ] P1 items in FIXES.md unchecked
- [ ] Any test failures in Phase 4
- [ ] `deploy-checker` verdict is FAIL or WARN
- [ ] New security findings introduced by P1 fixes (Phase 4 re-scan)

## Rollback

If a production deployment fails after merge:

```bash
# Git: revert the merge commit
git revert -m 1 HEAD && git push
```

Database: every destructive migration must have a paired rollback migration committed before release.

## Quality Guidelines

> [!CAUTION]
> **BLOCKING STEP.** Phase 2 requires explicit user approval before Phase 3 begins. Do not auto-advance past the P1/P2 summary. The user must approve proceeding.

> [!CAUTION]
> **BLOCKING STEP.** Phase 5 deploy-checker verdict must be PASS, not WARN. A WARN verdict means the environment has unresolved issues that can cause silent failures in production.

- MUST: follow `workflows/plan-and-execute.md` for multi-step orchestration context.
- MUST: apply `workflows/code-writing.md` reviewer gate at each fix boundary in Phase 3.
- MUST NOT: batch-fix multiple P1 items before running `tester`. One fix → verify → next fix.
- SHOULD: file `bd create` issues for all P2 items that are deferred past this release.

## References

- `workflows/full-audit.md` — Phase 1 of this workflow
- `workflows/code-writing.md` — mandatory at each Phase 3 fix boundary
- `workflows/plan-and-execute.md` — orchestration protocol for multi-step execution
- `skills/security-gate/SKILL.md` — Phase 4 parallel security gate (semgrep + codeql + supply-chain + insecure-defaults + security-auditor + differential-review)
- Agents: `coder`, `tester`, `security-auditor`, `deploy-checker`, `git-manager`, `debugger`

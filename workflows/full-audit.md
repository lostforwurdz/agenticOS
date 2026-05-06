---
description: Comprehensive parallel codebase audit across all quality dimensions. Run before major releases or as a periodic health check.
---

# /full-audit - Full Audit

A codebase that is only reviewed incrementally accumulates blind spots. The full audit closes that gap: every quality dimension is examined in parallel by a specialist, then a single consolidation pass deduplicates findings and assigns P1–P4 priorities. Without the consolidated `FIXES.md`, findings from one auditor get silently dropped when they overlap with another. Without the gate table, P1 items slip into releases.

## When To Use

- Before any major or production release (required gate).
- Weekly health check on long-running projects.
- After a large feature branch merges into main.
- When `workflows/release-prep.md` Phase 1 triggers it.
- Any time the codebase has not been fully reviewed in 30+ days.

## Workflow

### Phase 1: Parallel Audit

Dispatch **all 9 agents in a SINGLE message with multiple Task tool calls**. Do not dispatch sequentially — all must run in parallel.

| Agent | Output file | Focus |
|-------|-------------|-------|
| `reviewer` | `.claude/audits/AUDIT_CODE.md` | Code quality, patterns, differential-review on recent commits |
| `bug-auditor` | `.claude/audits/AUDIT_BUGS.md` | Runtime bugs, null refs, race conditions |
| `security-auditor` | `.claude/audits/AUDIT_SECURITY.md` | OWASP surface, semgrep, insecure-defaults, sarif-parsing |
| `docs-manager` | `.claude/audits/AUDIT_DOCS.md` | README gaps, inline doc coverage, API doc completeness |
| `deploy-checker` | `.claude/audits/DEPLOY_CHECK.md` | Config, env, dependencies, supply-chain-risk-auditor |
| `ui-auditor` | `.claude/audits/AUDIT_UI_UX.md` | Accessibility (WCAG), UI consistency |
| `perf-auditor` | `.claude/audits/AUDIT_PERF.md` | Performance regressions, N+1 patterns, bundle size |
| `seo-auditor` | `.claude/audits/AUDIT_SEO.md` | SEO optimization (web/PWA targets only; skip for non-web) |
| `api-tester` | `.claude/audits/API_TEST_REPORT.md` | API endpoint validation, contract coverage |

Prompt each agent: `"Audit [target directory]. Save report to [output file]."`

**Gate:** All 9 agents must produce output before Phase 2 starts. Partial results are noted but do not block consolidation — re-dispatch any failed agent individually.

### Phase 2: Consolidation

After all Phase 1 agents complete, dispatch `debugger` (sequential):

- Read all `.claude/audits/AUDIT_*.md` and `API_TEST_REPORT.md`
- Deduplicate findings that appear across multiple reports
- Apply priority framework: P1 Critical / P2 High / P3 Medium / P4 Low
- Write `.claude/audits/FIXES.md` in the schema below

### Phase 3: Present Summary

Orchestrator presents to user:

- P1 / P2 / P3 / P4 counts with estimated effort
- Recommended next action (proceed to `release-prep`, or run `coder` on P1 items first)

## FIXES.md Schema

```markdown
# Consolidated Fix Plan

Generated: [ISO timestamp]
Sources: AUDIT_CODE.md, AUDIT_BUGS.md, AUDIT_SECURITY.md, ...

## Summary
| Priority | Count | Est. Effort |
|----------|-------|-------------|
| P1 Critical | X | Xh |
| P2 High     | X | Xh |
| P3 Medium   | X | —  |
| P4 Low      | X | —  |

## P1 — Critical (fix before next commit)

### [ ] FIX-001: [Title]
**Source:** AUDIT_SECURITY.md
**Root cause:** one sentence
**File:** `src/path/file.ts:42`
**Fix:** step-by-step
**Verify:** `npm test -- related.test.ts`
```

## Gates

| Gate | Condition | Action if failed |
|------|-----------|-----------------|
| Phase 1 complete | All 9 agents produced output | Re-dispatch failed agents individually |
| P1 count = 0 | No critical findings | Proceed to `release-prep` |
| P1 count > 0 | Critical findings exist | Run `coder` on FIXES.md P1 items; re-audit affected areas |

## Quality Guidelines

> [!CAUTION]
> **BLOCKING STEP.** All Phase 1 agents MUST be dispatched in a single message as parallel Task calls. Sequential dispatch defeats the purpose of the workflow and doubles wall time. Do not start Phase 2 until all Phase 1 agents have returned output.

> [!CAUTION]
> **BLOCKING STEP.** Do not proceed to `release-prep` while P1 items remain unchecked in FIXES.md. P1 = release blocker, no exceptions.

- MAY: skip `seo-auditor` for non-web targets (native mobile-only, CLI tools, pure API services), but document the skip explicitly in the audit output.
- MUST NOT: combine Phase 1 and Phase 2 — consolidation requires all audit data first.
- SHOULD: after fixing P1 items, re-run the specific auditor that flagged them to confirm resolution.

## References

- `workflows/release-prep.md` — calls this workflow as its Phase 1
- `workflows/code-writing.md` — apply at each fix boundary after running `coder` on P1 items
- `skills/AUDIT.md` — per-auditor scope and invocation details
- Agents: `reviewer`, `bug-auditor`, `security-auditor`, `docs-manager`, `deploy-checker`, `ui-auditor`, `perf-auditor`, `seo-auditor`, `api-tester`, `debugger`, `coder`
- Note: `tester` is not dispatched by this workflow directly — it is dispatched downstream by `release-prep.md` Phase 4 when this workflow is invoked from there.

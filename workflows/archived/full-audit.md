# Full Audit Workflow

Comprehensive audit of the entire codebase. Run before major releases or as a weekly health check.

## Trigger
- Manual: Before major release
- Scheduled: Weekly health check

---

## Orchestrator Dispatch

The orchestrator invokes `superpowers:dispatching-parallel-agents` then runs two phases.

### Phase 1 — Parallel Audit (all agents start simultaneously)

| Agent | Scope | Output |
|-------|-------|--------|
| `security-auditor` | Full codebase — invokes `semgrep`, `insecure-defaults`, `sarif-parsing` | `.claude/audits/AUDIT_SECURITY.md` |
| `bug-auditor` | `src/` — invokes `superpowers:systematic-debugging` | `.claude/audits/AUDIT_BUGS.md` |
| `reviewer` | `src/` — invokes `differential-review` on latest commits | `.claude/audits/AUDIT_CODE.md` |
| `perf-auditor` | Full codebase | `.claude/audits/AUDIT_PERF.md` |
| `database-admin` | Database layer — schema, queries, N+1 patterns | `.claude/audits/AUDIT_DB.md` |
| `ui-auditor` | `mobile-app/src/` — a11y and consistency | `.claude/audits/AUDIT_UI_UX.md` |
| `api-tester` | `backend-service/src/routes/` | `.claude/audits/API_TEST_REPORT.md` |
| `deploy-checker` | Config, env, dependencies — invokes `supply-chain-risk-auditor` | `.claude/audits/DEPLOY_CHECK.md` |
| `docs-manager` | READMEs, inline docs, API docs | `.claude/audits/AUDIT_DOCS.md` |
| `seo-auditor` | PWA/web target only (`mobile-app/web/`) | `.claude/audits/AUDIT_SEO.md` |

**Gate:** All 10 agents must complete before Phase 2 starts. Partial results are noted but do not block consolidation.

### Phase 2 — Consolidation (sequential)

1. **`debugger`** — reads all `AUDIT_*.md` files, deduplicates findings across agents, applies priority framework (P1–P4), writes `.claude/audits/FIXES.md`
2. **Orchestrator** — presents summary to user: P1/P2/P3/P4 counts, estimated effort, recommended next action

---

## Execution Prompt

```
Run the full-audit workflow.

Phase 1 — dispatch in parallel:
- security-auditor: full codebase (semgrep + insecure-defaults + sarif-parsing)
- bug-auditor: src/ runtime bugs only
- reviewer: src/ code quality + differential-review on recent commits
- perf-auditor: full codebase
- database-admin: database layer audit
- ui-auditor: mobile-app/src/ a11y and consistency
- api-tester: backend-service/src/routes/ all endpoints
- deploy-checker: config + env + supply-chain-risk-auditor
- docs-manager: README and API doc gaps
- seo-auditor: mobile-app/web/ PWA target only

Phase 2 — after all complete:
- debugger: consolidate all AUDIT_*.md into FIXES.md (P1–P4 prioritized)

Save all reports to .claude/audits/
```

---

## Output Structure

```
.claude/audits/
├── AUDIT_SECURITY.md     ← security-auditor (semgrep + insecure-defaults)
├── AUDIT_BUGS.md         ← bug-auditor
├── AUDIT_CODE.md         ← reviewer
├── AUDIT_PERF.md         ← perf-auditor
├── AUDIT_DB.md           ← database-admin
├── AUDIT_UI_UX.md        ← ui-auditor
├── API_TEST_REPORT.md    ← api-tester
├── DEPLOY_CHECK.md       ← deploy-checker (+ supply-chain-risk-auditor)
├── AUDIT_DOCS.md         ← docs-manager
├── AUDIT_SEO.md          ← seo-auditor
└── FIXES.md              ← debugger consolidation (P1–P4)
```

---

## FIXES.md Format

```markdown
# Consolidated Fix Plan

Generated: [ISO timestamp]
Sources: AUDIT_SECURITY.md, AUDIT_BUGS.md, AUDIT_CODE.md, ...

## Summary
| Priority | Count | Est. Effort |
|----------|-------|-------------|
| P1 Critical | X | Xh |
| P2 High | X | Xh |
| P3 Medium | X | — |
| P4 Low | X | — |

## P1 — Critical (fix before next commit)

### [ ] FIX-001: [Title]
**Source:** AUDIT_SECURITY.md
**Root cause:** one sentence
**File:** `src/path/file.ts:42`
**Fix:** step-by-step
**Verify:** `npm test -- related.test.ts`
```

---

## Gates

| Gate | Condition | Action if failed |
|------|-----------|-----------------|
| Phase 1 complete | All 10 agents produced output | Re-dispatch failed agents individually |
| P1 count = 0 | No critical findings | Proceed to release-prep |
| P1 count > 0 | Critical findings exist | Run `coder` on FIXES.md P1 items, then re-audit |

---

## Post-Audit Actions

1. Review `FIXES.md` — confirm P1 priority assignments
2. Run `coder` on P1 items (one fix at a time)
3. Run `tester` after each fix
4. Re-run affected auditor to confirm resolution
5. When P1 = 0 → proceed to `release-prep`

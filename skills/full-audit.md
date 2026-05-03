---
name: full-audit
description: Run all audit agents in parallel, then consolidate findings with debugger
---

# Full Audit Workflow

Run a comprehensive audit of the entire codebase. Use before major releases or as a weekly health check.

## Phase 1: Parallel Audit

Spawn ALL of the following agents **in parallel** (single response with multiple Task calls):

| Agent | Output File | Focus |
|-------|-------------|-------|
| `reviewer` | `.claude/audits/AUDIT_CODE.md` | Code quality (absorbs code-auditor) |
| `bug-auditor` | `.claude/audits/AUDIT_BUGS.md` | Runtime bugs |
| `security-auditor` | `.claude/audits/AUDIT_SECURITY.md` | OWASP deep scan |
| `docs-manager` | `.claude/audits/AUDIT_DOCS.md` | Documentation gaps (absorbs doc-auditor) |
| `deploy-checker` | `.claude/audits/AUDIT_INFRA.md` | Infrastructure, env, dependencies (absorbs infra-auditor, env-validator, dep-auditor) |
| `ui-auditor` | `.claude/audits/AUDIT_UI_UX.md` | UI/UX and accessibility |
| `perf-auditor` | `.claude/audits/AUDIT_PERF.md` | Performance issues |
| `seo-auditor` | `.claude/audits/AUDIT_SEO.md` | SEO optimization |
| `api-tester` | `.claude/audits/API_TEST_REPORT.md` | API validation |

Each agent targets the project's source code. Provide each with a prompt like:
```
Audit [target directory]. Save report to [output file].
```

## Phase 2: Consolidation

After **all** auditors complete, spawn:
- `debugger` - Read all `.claude/audits/AUDIT_*.md` files and create `.claude/audits/FIXES.md` with prioritized action items (absorbs fix-planner)

## Post-Audit Actions

1. Review `FIXES.md` - Prioritize based on your timeline
2. Run `coder` - Implement P1 (critical) fixes
3. Run `tester` - Verify fixes work
4. Re-audit affected areas if needed

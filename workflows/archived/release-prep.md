# Release Prep Workflow

Full pre-release pipeline: audit → fix → verify → deploy-gate → PR. Nothing ships with P1 issues.

## Trigger
- Manual: Before production release

---

## Orchestrator Dispatch

The orchestrator invokes `superpowers:executing-plans` then coordinates 6 sequential phases.

---

### Phase 1 — Full Audit (parallel)

Dispatch all auditors simultaneously. Same as `full-audit` workflow.

| Agent | Output |
|-------|--------|
| `security-auditor` | `AUDIT_SECURITY.md` (semgrep + insecure-defaults + sarif-parsing) |
| `bug-auditor` | `AUDIT_BUGS.md` |
| `reviewer` | `AUDIT_CODE.md` (differential-review on all commits since last release) |
| `perf-auditor` | `AUDIT_PERF.md` |
| `database-admin` | `AUDIT_DB.md` |
| `ui-auditor` | `AUDIT_UI_UX.md` |
| `api-tester` | `API_TEST_REPORT.md` |
| `deploy-checker` | `DEPLOY_CHECK.md` (supply-chain-risk-auditor included) |
| `docs-manager` | `AUDIT_DOCS.md` |
| `seo-auditor` | `AUDIT_SEO.md` (PWA only) |

**Gate:** All 10 complete → proceed to Phase 2.

---

### Phase 2 — Fix Planning (sequential)

**`debugger`** consolidates all `AUDIT_*.md` into `.claude/audits/FIXES.md` (P1–P4 prioritized).

**Present to user:**
- P1 count (release blockers)
- P2 count (should fix)
- Estimated total effort

**Gate:** User reviews FIXES.md and approves proceeding.

---

### Phase 3 — Fix P1 Items (sequential, one at a time)

**`coder`** works through FIXES.md P1 items only. For each fix:
- Read FIXES.md entry
- Implement minimal fix (no scope creep)
- Invoke `superpowers:verification-before-completion`
- Mark `[x]` in FIXES.md
- Hand off to tester before next fix

**Gate:** Zero P1 items remain unchecked.

---

### Phase 4 — Verification (parallel)

| Agent | Scope |
|-------|-------|
| `tester` | Full suite — tsc + lint + npm test. All must pass. |
| `security-auditor` | Re-scan changed files only (differential-review mode) |

**Gate:** 0 test failures + 0 new security findings in changed files.

---

### Phase 5 — Deploy Validation (sequential)

**`deploy-checker`** runs full pre-deploy check:
- Build, env, dependency health, supply-chain-risk-auditor
- Railway-specific: railway.toml, PORT, /health endpoint

**Gate:** Verdict must be PASS (not WARN). No exceptions for release.

---

### Phase 6 — Release PR (sequential)

**`git-manager`** invokes `superpowers:finishing-a-development-branch`:
1. Verifies tests pass
2. Presents 4 options — user selects "Push and create PR"
3. PR description includes: summary of changes, fixes applied, test results, deploy checklist

---

## Release Blockers (will not ship if any are true)

- [ ] P1 items in FIXES.md unchecked
- [ ] Any test failures
- [ ] deploy-checker verdict: FAIL
- [ ] Critical finding in post-fix security re-scan
- [ ] Railway health check not instant

---

## Execution Prompt

```
Run the release-prep workflow for version [X.Y.Z].

Phase 1 — full audit (parallel, all 10 auditors)
Phase 2 — debugger consolidates FIXES.md, present P1/P2 summary
Phase 3 — coder fixes P1 items one at a time (await each before next)
Phase 4 — tester + security-auditor re-scan in parallel
Phase 5 — deploy-checker full Railway validation
Phase 6 — git-manager creates release PR via finishing-a-development-branch skill

Block at each gate. Do not advance phases with unresolved blockers.
```

---

## Rollback

If production deployment fails after merge:

```bash
# Railway: redeploy previous successful build from dashboard
# Git: revert merge commit
git revert -m 1 HEAD && git push
```

Database: every destructive migration must have a paired rollback migration committed before release.

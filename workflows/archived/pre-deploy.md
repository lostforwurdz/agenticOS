# Pre-Deploy Workflow

Final validation gate before any production deployment to Railway.

## Trigger
- Manual: Before deploying to Railway
- CI/CD: Part of deployment pipeline

---

## Orchestrator Dispatch

The orchestrator invokes `superpowers:dispatching-parallel-agents`.

### Phase 1 — Parallel (start simultaneously)

| Agent | Scope | Gate condition |
|-------|-------|---------------|
| `deploy-checker` | Build + env vars + dependency audit + `supply-chain-risk-auditor` + Railway config | Verdict: PASS |
| `security-auditor` | `insecure-defaults` scan only (fast mode — no full semgrep) | 0 Critical findings |
| `tester` | Full test suite — tsc + lint + npm test | 0 failures |

### Phase 2 — Gate (sequential, after all complete)

| Outcome | Action |
|---------|--------|
| All pass | "READY TO DEPLOY" |
| deploy-checker: FAIL | BLOCKED. Do not deploy. Fix listed blockers. |
| security-auditor: Critical | BLOCKED. Critical security finding blocks deployment. |
| tester: failures | BLOCKED. Failing tests block deployment. |
| deploy-checker: WARN | Proceed with warnings documented |

---

## Execution Prompt

```
Run the pre-deploy workflow before deploying to Railway.

Phase 1 — dispatch in parallel:
- deploy-checker: build validation + all env vars present + npm audit + supply-chain-risk-auditor + railway.toml valid + health endpoint instant
- security-auditor: insecure-defaults fast scan only (no full semgrep)
- tester: full suite (tsc + lint + npm test)

Phase 2 — gate:
- All pass → READY TO DEPLOY
- Any blocker → BLOCKED, list what must be fixed before deployment
```

---

## Expected Output

```markdown
# Pre-Deploy Check

## Verdict: READY | BLOCKED

### Build & Config (deploy-checker)
- [x] TypeScript compiles clean
- [x] All env vars present
- [x] No hardcoded secrets
- [x] npm audit: 0 critical/high CVEs
- [x] supply-chain-risk-auditor: no abandoned packages
- [x] railway.toml present and valid
- [x] /health endpoint: instant response (no DB call)
- [x] PORT matches Dockerfile EXPOSE

### Security Fast Scan (security-auditor)
- [x] insecure-defaults: no fail-open configs
- [x] No hardcoded credentials detected

### Tests (tester)
- [x] Types: clean
- [x] Lint: clean
- [x] Tests: 87/87 pass

## Decision
READY TO DEPLOY
```

---

## Railway Rollback

If deployment fails after going live:

```bash
# Redeploy previous successful build via Railway dashboard
# Or revert the commit and push:
git revert HEAD
git push
```

Database migrations: always have a rollback migration ready before applying destructive changes.

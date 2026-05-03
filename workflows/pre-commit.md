# Pre-Commit Workflow

Fast quality gate before every commit. Parallel where possible, sequential where gates apply.

## Trigger
- Manual: Before committing
- Automated: Git pre-commit hook

---

## Orchestrator Dispatch

The orchestrator invokes `superpowers:dispatching-parallel-agents`.

### Phase 1 — Parallel (start simultaneously)

| Agent | Scope | Gate condition |
|-------|-------|---------------|
| `reviewer` | Staged files — code quality + `differential-review` on the diff | No Critical issues |
| `tester` | Full test suite — `npx tsc --noEmit`, `npm run lint`, `npm test` | 0 failures |

### Phase 2 — Decision (sequential, after both complete)

| Outcome | Action |
|---------|--------|
| Both pass | "Ready to commit" — proceed |
| reviewer: Critical | Block. List issues. Do not commit. |
| tester: failures | Block. List failures with file:line. Do not commit. |
| reviewer: Warning only | Proceed with warnings logged |

---

## Execution Prompt

```
Run the pre-commit workflow on staged changes.

Phase 1 — dispatch in parallel:
- reviewer: check staged files for Critical issues; run differential-review on the diff
- tester: run full suite (tsc + lint + npm test)

Phase 2 — gate:
- If any Critical issues or test failures → BLOCKED, list what must be fixed
- If only Warnings → PROCEED, log warnings
- If all pass → PROCEED
```

---

## Expected Output

```markdown
# Pre-Commit Check

## Verdict: PASS | BLOCKED

### Code Review (reviewer)
- [x] No Critical issues
- [x] differential-review: no new attack surface
- [ ] Warning: `src/routes/wager.ts:47` — missing null check on optional field

### Tests (tester)
- [x] Types: clean
- [x] Lint: clean
- [x] Tests: 87/87 pass

## Decision
PASS — 1 warning logged, proceeding with commit.
```

---

## Quick Manual Alternative

If not using agents:

```bash
npx tsc --noEmit && npm run lint && npm test
```

All three must exit 0 before committing.

---

## Git Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
npx tsc --noEmit && npm run lint && npm test
if [ $? -ne 0 ]; then
  echo "Pre-commit checks failed. Fix before committing."
  exit 1
fi
```

---
name: security-gate
description: >-
  Pre-merge security gate for auth/secrets diffs. Fans out 4 registered
  security skills + security-auditor agent in parallel; differential-review
  consolidates findings into a severity verdict. Invoke before merging diffs
  that touch auth, secrets, payment, or API gateway code, and before any
  release tag. Produces a consolidated SECURITY_GATE report.
---

# Security Gate

Pre-merge security gate. Fans out parallel analysis across all registered security tools, then consolidates into a single severity verdict via `differential-review`.

## Trigger

Invoke when:
- A diff touches auth, secrets, payment flows, or API gateway code.
- A release tag is about to be created.
- Any change classified as high-risk in `workflows/code-writing.md`.

## Phase 1 — Parallel Fan-out

> [!CAUTION]
> **BLOCKING STEP.** Dispatch all 5 agents/skills in a SINGLE message with multiple Task tool calls. Do not dispatch sequentially — that defeats the purpose of the parallel gate.

Dispatch all 5 in a SINGLE message with multiple Task tool calls:

| Dispatch | Type | Output |
|---|---|---|
| `semgrep` skill | security scan | SARIF findings |
| `codeql` skill | deep taint analysis | SARIF findings |
| `supply-chain-risk-auditor` skill | dependency risk | markdown report |
| `insecure-defaults` skill | fail-open / hardcoded secrets | markdown findings |
| `security-auditor` agent | holistic OWASP review | markdown findings |

Wait for ALL 5 to complete before proceeding to Phase 2.

## Phase 2 — Consolidation (sequential)

Wait for Phase 1 to complete. Dispatch the `differential-review` skill with all Phase 1 outputs as input. Provide:
- All SARIF files and markdown findings from Phase 1.
- The diff or PR under review.

`differential-review` produces a consolidated severity verdict: **Critical / Important / Suggestions**.

> [!CAUTION]
> **BLOCKING STEP.** If `differential-review` returns any Critical finding, halt. Do not merge until all Critical findings are resolved and Phase 1 + Phase 2 are re-run.

## Verification

- [ ] All 5 Phase 1 outputs exist (SARIF or markdown per tool).
- [ ] `differential-review` verdict written to `.claude/security/SECURITY_GATE_<timestamp>.md`.
- [ ] No Critical findings in the consolidated verdict (or findings documented with resolution).

## References

- `workflows/code-writing.md` — normal reviewer gate for non-security changes
- `workflows/plan-and-execute.md` — Phase 7 applies this skill at security-sensitive phase boundaries

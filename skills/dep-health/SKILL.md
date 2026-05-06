---
name: dep-health
description: >-
  Parallel dependency health check. Fans out dependency-manager agent,
  supply-chain-risk-auditor skill, and compliance-auditor agent in parallel;
  debugger agent consolidates into a prioritized upgrade plan. Invoke weekly
  (scheduled) or when diffs touch package.json, requirements.txt,
  pyproject.toml, go.mod, or Cargo.toml. Produces DEP_HEALTH report with
  three audit sections and a consolidated upgrade plan.
---

# Dependency Health Check

Parallel health check across three lenses (upgrade status, supply-chain risk, compliance), consolidated into a single prioritized upgrade plan.

## Trigger

Invoke when:
- Weekly scheduled run (dependency hygiene cadence).
- A diff touches `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, or `Cargo.toml`.

## Phase 1 — Parallel Audit

> [!CAUTION]
> **BLOCKING STEP.** Dispatch all 3 agents/skills in a SINGLE message with multiple Task tool calls. Do not dispatch sequentially.

Dispatch all 3 in a SINGLE message with multiple Task tool calls:

| Dispatch | Type | Output |
|---|---|---|
| `dependency-manager` agent | outdated/breaking upgrades | markdown report |
| `supply-chain-risk-auditor` skill | typosquatting, abandoned, compromised packages | markdown report |
| `compliance-auditor` agent | license compatibility, policy violations | markdown report |

Wait for ALL 3 to complete before proceeding to Phase 2.

## Phase 2 — Consolidation (sequential)

Wait for Phase 1 to complete before dispatching Phase 2.

Dispatch the `debugger` agent with all three Phase 1 reports as input. The `debugger` agent produces a consolidated upgrade plan with actions prioritized as:

1. **Security** — packages with known CVEs or supply-chain risk (fix immediately).
2. **Major** — breaking-version upgrades requiring code changes (schedule sprint work).
3. **Minor / Patch** — safe upgrades (batch into next maintenance window).

## Verification

- [ ] `.claude/audits/DEP_HEALTH_<timestamp>.md` exists.
- [ ] Report contains three sections: Dependency Status, Supply-Chain Risk, Compliance.
- [ ] Consolidated upgrade plan present with Security / Major / Minor priority buckets.

## References

- `workflows/plan-and-execute.md` — use this skill as a pre-execution health check when plans introduce new dependencies

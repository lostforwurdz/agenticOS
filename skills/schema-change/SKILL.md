---
name: schema-change
description: >-
  Database migration safety gate. Sequential chain with embedded parallel
  audit. Invokes parallel postgres-pro + compliance-auditor for migration
  safety, then debugger consolidates, then dual-review for high-stakes
  approval, then deploy-checker verifies rollback migration exists. Invoke
  automatically when diffs touch migrations/, schema.ts, *.sql, drizzle/,
  or any file containing createTable/alterTable/dropColumn. Wrong schema
  changes are operationally hardest to reverse — this gate is mandatory
  for migration PRs.
---

# Schema Change Gate

Mandatory safety gate for database migrations. Parallel audit embedded inside a sequential four-phase chain; rollback migration is a hard requirement.

## Trigger

Invoke when a diff touches `migrations/`, `drizzle/`, `schema.ts`, any `*.sql` file, or any file containing `createTable`, `alterTable`, or `dropColumn`.

## Phase 1 — Parallel Migration Audit

> [!CAUTION]
> **BLOCKING STEP.** Dispatch both agents in a SINGLE message with multiple Task tool calls. Do not dispatch sequentially.

| Dispatch | Type | Output |
|---|---|---|
| `postgres-pro` agent | Migration safety (reversibility, locking, data loss risk) | markdown report |
| `compliance-auditor` agent | Schema policy (naming, PII fields, audit columns) | markdown report |

Wait for BOTH to complete before proceeding to Phase 2.

## Phase 2 — Consolidation (sequential)

Wait for Phase 1. Dispatch `debugger` agent with both reports. Verdict: **Safe** (proceed), **Requires Changes** (halt and fix), or **Critical** (halt immediately).

> [!CAUTION]
> **BLOCKING STEP.** Critical verdict halts the chain — redesign and re-run Phases 1–2 before proceeding.

## Phase 3 — High-Stakes Review (sequential)

Wait for Phase 2 Safe verdict. Dispatch `dual-review` skill with migration diff and Phase 1–2 reports. Wait for Approved.

## Phase 4 — Rollback Verification (sequential)

Wait for Phase 3 Approved. Dispatch `deploy-checker` agent to verify a rollback (down) migration exists for every forward (up) migration in the PR.

> [!CAUTION]
> **BLOCKING STEP.** No rollback migration found: halt until one is added.

## Verification

- [ ] Phase 1: `postgres-pro` and `compliance-auditor` reports exist.
- [ ] Phase 2: `debugger` verdict is Safe.
- [ ] Phase 3: `dual-review` returned Approved.
- [ ] Phase 4: `deploy-checker` confirmed rollback present for every forward migration.

## References

- `agents/postgres-pro.md` — migration safety and locking analysis
- `agents/compliance-auditor.md` — schema policy compliance
- `agents/debugger.md` — consolidation and verdict agent
- `agents/deploy-checker.md` — rollback migration verification
- `skills/dual-review/SKILL.md` — high-stakes parallel review

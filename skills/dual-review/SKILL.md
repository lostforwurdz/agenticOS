---
name: dual-review
description: >-
  High-stakes parallel review. Dispatches local reviewer agent and Gemini
  consult_peer (strict-reviewer skill) in parallel via gemini-router; the
  orchestrator synthesizes both verdicts. Invoke manually for auth, payment,
  encryption, schema migrations, or any change touching production data
  integrity. Produces a DUAL_REVIEW report with both verdicts side-by-side
  and an orchestrator synthesis section.
---

# Dual Review

High-stakes parallel review combining a local `reviewer` agent and a Gemini-side `strict-reviewer`. The orchestrator synthesizes both verdicts.

## Trigger

Invoke manually when the change touches: authentication, payment processing, encryption/key management, database schema migrations affecting production data integrity, or any change classified high-stakes in `workflows/code-writing.md`.

## Phase 1 — Parallel Dual Review

> [!CAUTION]
> **BLOCKING STEP.** Dispatch both reviewers in a SINGLE message with multiple Task tool calls. Do not dispatch sequentially — the independence of the two reviewers is the guarantee.

Dispatch all 2 agents/skills in a SINGLE message with multiple Task tool calls:

| Dispatch | Output |
|---|---|
| `reviewer` agent (local Claude) | severity-bucketed findings + Approve / Request Changes verdict |
| `gemini-router` skill → `agent-pool` `consult_peer` with `strict-reviewer` | Critical / Important / Suggestions + Approve / Request Changes / Major Rework verdict |

For the Gemini dispatch: invoke `gemini-router` skill; it selects `consult_peer` with `strict-reviewer` loaded. Provide the full diff and relevant context files.

Wait for BOTH to complete before Phase 2.

## Phase 2 — Synthesis (sequential)

The orchestrator synthesizes both verdicts. If reviewers agree: record consensus. If they disagree on Critical findings:

> [!CAUTION]
> **BLOCKING STEP.** Surface the disagreement to the user with BOTH arguments verbatim. Do not silently resolve Critical disagreements.

Write `.claude/audits/DUAL_REVIEW_<timestamp>.md` with both verdicts side-by-side and a synthesis section (agreement map, unresolved disagreements, final recommendation).

## Verification

- [ ] `.claude/audits/DUAL_REVIEW_<timestamp>.md` exists with both verdicts and synthesis section.
- [ ] No Critical findings left unresolved or silently dismissed.

## References

- `skills/gemini-router/SKILL.md` — Gemini routing policy
- `workflows/code-writing.md` — standard reviewer gate for non-high-stakes changes
- `workflows/plan-and-execute.md` — use this skill at Phase 7 for high-stakes plan phases

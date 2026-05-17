---
name: 3d-review
description: >-
  Three-dimensional code review: primary reviewer (full repo context) + cold-read reviewer
  (no prior context, fresh eyes) + debugger synthesizer (reconciles agreement, surfaces
  disagreements, produces verdict). Invoke for any non-trivial diff, especially
  high-stakes changes (auth, payment, encryption, schema migrations, security fixes,
  multi-agent batch work). Three independent perspectives catch what any one reviewer
  misses — primary leverages repo conventions, cold-read catches normalization blind
  spots, synthesizer prevents silent disagreement resolution.
---

# 3D Review

Three independent review dimensions over the same diff. Three agents, three perspectives, one synthesized verdict.

## Why "3D"

A single reviewer misses things they've normalized to. Two reviewers can disagree without anyone noticing — the louder one wins. **Three dimensions plus synthesis forces every disagreement into the open:**

1. **Primary** — reviewer agent with full repo context, knows conventions and history
2. **Cold-read** — fresh-eyes reviewer with no prior context, assumes nothing, catches subtle bugs the primary normalized to
3. **Synthesizer** — debugger agent that reconciles findings, surfaces unresolved Critical disagreements, produces final verdict

Empirically: cold-read reviewers consistently catch Wave-N regressions, dead-code shipping, route mismatches, and "fix-shaped code that doesn't deliver" that primary reviewers miss because the primary's context makes them trust commit messages.

## When to Invoke

- Any diff touching authentication, payment, encryption, key management, secrets store, or schema migrations (auto-invoke)
- Multi-agent batch work where workspace state drift may have caused regressions (e.g. parallel worktree dispatches)
- Any commit whose body lists "fixes 10+ issues" — synthesis catches when some don't actually deliver
- Before merging any branch with >300 LOC delta
- When `pre-commit` skill or `release-prep` workflow is gating a merge
- Whenever you'd otherwise rely on a single reviewer for a non-trivial change

## How

Use the registered pipeline `3d-review` via `pool_pipeline_run`. Pipeline definition lives at `~/loom/pipelines/3d-review.json`.

```
pool_pipeline_run({ pipeline_id: "3d-review" })
```

The pipeline runs three steps:

| Step | Role | Routing |
|---|---|---|
| `reviewer-primary` | severity-bucketed findings + Approve/Request Changes/Major Rework | `reviewer` agent (local Claude) |
| `reviewer-coldread` | fresh-eyes pass, no prior context, independent verdict | `routing_hint: ["code-review", "large-context-summary"]` — prefers non-Claude 1M-context substrate |
| `synthesize` | Agreement map, primary-only, cold-only, unresolved Critical disagreements, final recommendation | `debugger` agent (on `on_complete_all` trigger) |

The pipeline runner auto-prepends the two reviewer outputs to the synthesizer's system prompt — the synthesizer reads both verbatim before reconciling.

## Output Format

Synthesizer produces:

1. **AGREEMENT MAP** — findings BOTH reviewers flagged (highest signal — must address before merge)
2. **PRIMARY-ONLY FINDINGS** — only primary flagged. Likely valid (has repo context). Verify before dismissing.
3. **COLDREAD-ONLY FINDINGS** — only cold-read flagged. Cold eyes caught something. Investigate; may be a project convention the primary reviewer normalized to.
4. **UNRESOLVED DISAGREEMENTS** — places where the two reviewers contradict on Critical-severity findings. Surface BOTH arguments verbatim. The synthesis's most important job: never silently pick one side.
5. **FINAL RECOMMENDATION** — Approve / Request Changes / Major Rework. If unresolved Critical disagreements exist, the verdict is **NEEDS HUMAN ARBITRATION**.

## Verification

After invoking:

- [ ] Pipeline run completes (`pool_pipeline_get_run` shows `completed`)
- [ ] Synthesis step output exists and contains all 5 sections
- [ ] No Critical findings left unresolved
- [ ] If `NEEDS HUMAN ARBITRATION` verdict: human reviews the disagreement before merge proceeds

## Notes

- The pipeline currently has no per-run input mechanism — it runs against the daemon's default workspace. To review a specific branch, set up a pre-step that writes the diff to the pipeline workspace or use direct Agent dispatch for per-branch reviews until the pipeline gains input plumbing.
- Cold-read independence is the value proposition. Do not collapse to a single reviewer "for speed" on high-stakes changes — that's exactly when the catch matters.
- If the primary reviewer fully agrees with cold-read on Approve, the synthesizer should still run — its job is to verify agreement is real, not assumed.

---
description: Required for any multi-step task. Enter plan mode, write a plan file, get approval, dispatch implementation to specialist subagents per phase.
---

# /plan-and-execute - Plan and Execute

The user mandate of 2026-05-05: multi-step actions require written plans and subagent dispatch. An orchestrator that improvises a multi-step procedure without a plan file is flying blind — it cannot verify drift, cannot hand off mid-task, and cannot recover cleanly if something goes wrong. The plan file is the contract: it names who does what, in what order, with what acceptance criteria. The orchestrator sequences and verifies; specialists implement.

## When To Use

- Any task with more than one logical step.
- Any change that touches more than two files.
- Any task that introduces an architectural change, new dependency, or new abstraction.
- Any task with unclear scope or competing valid approaches.
- Any request that `workflows/session-start.md` Phase 3 routes here.

## Workflow

### Phase 1: Enter plan mode

1. Call `EnterPlanMode`. In plan mode, the orchestrator may only perform read-only exploration and edit the plan file. No implementation file writes in plan mode.
2. State to the user: "Entering plan mode for [task description]. I will explore, write a plan, and wait for your approval before executing."

### Phase 2: Explore

1. Dispatch up to 3 `Explore` subagents in parallel for broad scoping. Use 1 if the scope is contained; use 3 for architectural or cross-cutting changes.
2. Typical explore tasks:
   - Existing patterns in the codebase relevant to this change.
   - Prior solutions or utilities that can be reused (check `bd remember` keys first).
   - Blast radius: what other files or systems does the change touch?
3. Synthesize the explore output. Do not proceed to Phase 3 until all explore agents have returned.

### Phase 3: Design (optional)

1. If the approach is non-obvious or has meaningful trade-offs, dispatch a `planner` agent or a domain specialist (e.g., `nextjs-developer`, `react-specialist`, `database-admin`) with the explore output and task constraints.
2. Ask it to pressure-test the proposed approach: "Is this the right pattern? What are the risks? What would you do differently?"
3. Incorporate the design feedback into the plan file. Document the rejected alternatives and why.

### Phase 4: Write the plan file

1. Write the plan file to the path the harness specifies, typically `~/.claude/plans/<name>.md`. If no path is specified, use `~/.claude/plans/<slug>.md` where slug is a 2–3 word kebab-case description.
2. The plan file MUST include these sections:
   - **Context** — what problem this solves and why now.
   - **Constraints** — standing rules, performance targets, backward-compat requirements, out-of-scope items.
   - **Decisions** — resolved choices made during explore/design; rejected alternatives with reasons.
   - **File Manifest** — every file to be created or modified, organized by phase.
   - **Implementation Order** — phases listed in sequence; each phase names its specialist subagent and its deliverable.
   - **Verification** — how to confirm the implementation is correct (commands to run, behaviors to observe).
   - **Out of Scope** — explicit list. Follow-up items go to `bd create` at PR close.
   - **Risks** — known unknowns and open assumptions.
3. Each phase in Implementation Order must name its specialist subagent explicitly. "Orchestrator does it" is not valid for implementation phases.

### Phase 5: Exit plan mode

1. Call `ExitPlanMode`.
2. Present the plan to the user: summary of phases, specialist assignments, and verification criteria.
3. Wait for explicit user approval. Do NOT begin execution before approval. "Looks good", "proceed", "go ahead", or equivalent counts.

### Phase 6: Execute via dispatched specialists

1. For each phase in the plan's Implementation Order, dispatch the named specialist subagent. Provide each specialist with:
   - Relevant file paths (absolute).
   - A pointer to the plan file.
   - The constraints section.
   - The acceptance checklist for their phase.
2. Dispatch phases sequentially unless the plan explicitly marks phases as parallelizable. Do not start Phase N+1 until Phase N is verified.
3. The orchestrator does NOT write implementation files itself (except the plan file). Specialist dispatch is mandatory per phase.

### Phase 7: Apply code-writing at each phase boundary

1. After each specialist subagent returns, run `workflows/code-writing.md` before launching the next phase:
   - Dispatch the appropriate reviewer (see `code-writing.md` Phase 2).
   - Address findings.
   - Run the full test suite.
   - Commit at the phase boundary.
2. Do not batch commits across multiple phases. Each phase gets its own commit. This keeps the PR diff reviewable in logical chunks.

### Phase 8: Verify completion

1. Run every command in the plan file's Verification section.
2. Confirm all acceptance criteria from each phase are met.
3. If any verification step fails, do not declare the plan complete — diagnose, fix, re-verify.
4. File follow-up `bd create` issues for every item in the plan's Out of Scope section.

## Quality Guidelines

> [!CAUTION]
> **BLOCKING STEP.** Do not skip Phase 1. Multi-step actions without `EnterPlanMode` violate the 2026-05-05 mandate. If you find yourself writing implementation files without a plan file on disk, stop and retroactively write the plan before continuing.

> [!CAUTION]
> **BLOCKING STEP.** The orchestrator cannot write implementation files itself (except the plan file). Specialist subagent dispatch is mandatory per implementation phase. If the orchestrator is writing code, it is violating this workflow.

- MUST: plan files name their specialist subagent per phase explicitly. "TBD" is not a valid subagent assignment.
- MUST: review-test-commit at every phase boundary, not at the end. A plan with 4 phases produces 4 commits.
- MUST NOT: begin execution before ExitPlanMode + explicit user approval.
- SHOULD: keep plans in `~/.claude/plans/` for the duration of the task so they can be resumed if the session is interrupted.
- SHOULD: if scope expands during execution (a phase reveals more work than anticipated), pause, update the plan file, and surface the scope change to the user before continuing.

## References

- `workflows/code-writing.md` — mandatory at every phase boundary (Phase 7 of this workflow)
- `workflows/session-start.md` — Phase 3 routes multi-step requests here
- `workflows/session-close.md` — runs after all plan phases complete and verification passes
- `CLAUDE.md` — `## Standing Instructions` #6 ("Permanent orchestrator") and the new #7 ("Plan + subagent rule")

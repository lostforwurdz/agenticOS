---
name: gemini-router
description: Decision policy for when and how to invoke Gemini via agent-pool. Use whenever you're considering calling delegate_task, delegate_task_readonly, or consult_peer. Picks the right Gemini-side skill (tdd-planner / strict-reviewer / no skill) based on task shape, and tells you when NOT to delegate.
---

# Gemini Router

Decides which Gemini flow (if any) to use when offloading work from Claude Code via the `agent-pool` MCP.

## Decision tree

### 1. Code review / critique?
**→ `consult_peer` with the `strict-reviewer` skill loaded**
- Examples: "review this implementation", "is this secure?", "what bugs do you see?"
- Output: severity-bucketed review with Approve / Request Changes / Major Rework verdict
- Use `consult_peer` (not `delegate_task`) so Claude stays in the loop for synthesis

### 2. Implementation plan request?
**→ `delegate_task` with the `tdd-planner` skill loaded**
- Examples: "plan this refactor", "write a TDD plan for X", "how do I implement Y?"
- Output: checkbox-style plan with exact code, tests, commit steps
- Use full `delegate_task` (not readonly) because plans should ground in real files

### 3. Large-context analysis (input > 50K tokens)?
**→ `delegate_task_readonly` with no specific skill (Gemini's 1M context is the lever)**
- Examples: "summarize this 200-page doc", "find inconsistencies across these 50 files", "audit this whole repo"
- Use `_readonly` to prevent unintended writes during exploration

### 4. Quick second opinion / sanity check?
**→ `consult_peer` with no skill (pure Q&A)**
- Examples: "is this approach safe?", "any issues with this design?", "would you do this differently?"
- Faster than tdd-planner, lighter than strict-reviewer

### 5. Web search with grounding?
**→ Don't use agent-pool; use Gemini CLI's native Google Search grounding via raw `gemini -p`**
- Examples: any task where freshness matters and web sources need citation
- agent-pool's worker doesn't expose Google Search grounding tool by default; the raw CLI does

### 6. Otherwise — just write it in Claude
**→ Don't delegate trivial tasks. Each Gemini call has overhead.**

## When NOT to delegate

- The task touches files Claude can read directly without bloating context (use `Read` instead — cheaper)
- Tight code-generation loops where Claude's lower latency wins
- Task requires Claude-specific knowledge: other agents, beads, MCP setup, this repo's structure
- Anything under ~3 minutes of expected work

## Quick mapping

| Task | Verb | Skill | Notes |
|---|---|---|---|
| Plan a multi-file feature | `delegate_task` | `tdd-planner` | grounded in repo |
| Critique my code | `consult_peer` | `strict-reviewer` | sync return |
| Audit huge doc set | `delegate_task_readonly` | (none) | leverage 1M ctx |
| Sanity-check a plan | `consult_peer` | (none) | quick yes/no/why |
| Web research with citations | raw `gemini -p` | n/a | uses Google grounding |
| <2 min of code | (don't delegate) | n/a | Claude handles |

## Constraints

- Each `delegate_task` spawns a Gemini CLI worker that consumes from your Pro quota — not free at scale
- Cap at ~3 concurrent workers without explicit reason (free tier: 3, Pro: 15, Ultra: 60)
- For sequential dependent steps, use `create_pipeline` instead of N parallel `delegate_task` calls
- Verify Gemini's output before acting: it can hallucinate runtime context (it's not in this Claude session and doesn't share state)

---
description: Parallel pre-commit quality gate: reviewer + tester in one message, then triage. Blocks commit on Critical findings or test failures.
---

# /pre-commit - Pre-Commit

The per-change reviewer in `workflows/code-writing.md` runs during development, after the code is written. This workflow is a batch gate on staged files — it runs immediately before `git commit` and checks the full diff as a unit. The two workflows are complementary: code-writing gates individual changes mid-stream; pre-commit gates the staged snapshot before it becomes a commit. Running them in parallel (not sequentially) keeps the gate fast enough to use consistently.

## When To Use

- Immediately before every `git commit`.
- When `workflows/code-writing.md` Phase 5 directs you here before committing.
- As a manual check when the staged diff is large or spans multiple files.
- When uncertain whether a change is safe to commit without a second look.

## Workflow

### Phase 1: Parallel Dispatch

Dispatch `reviewer` AND `tester` in a **single message** with two Task tool calls. Do not run them sequentially.

| Agent | Scope | Gate condition |
|-------|-------|---------------|
| `reviewer` | Staged files — code quality, patterns, differential-review on the staged diff | No Critical issues |
| `tester` | Full test suite — tsc + lint + all tests | Zero failures |

Provide both agents with: the list of staged files (absolute paths) and a brief description of what changed and why.

### Phase 2: Triage Outcomes

After both agents return, apply this decision table:

| Outcome | Action |
|---------|--------|
| Both pass | "Ready to commit" — proceed with `git commit` |
| `reviewer`: Critical | BLOCKED. List every Critical issue. Do not commit until resolved. |
| `tester`: failures | BLOCKED. List failures with file:line. Do not commit until resolved. |
| `reviewer`: Warning only | PROCEED with warnings logged in commit body |
| `tester`: pre-existing failures unrelated to staged change | PROCEED — document in commit body, file `bd create` issue |

### Phase 3: Report

Emit a structured report before the commit verdict:

```markdown
# Pre-Commit Check

## Verdict: PASS | BLOCKED

### Code Review (reviewer)
- [x] No Critical issues
- [ ] Warning: `src/routes/wager.ts:47` — missing null check on optional field

### Tests (tester)
- [x] Types: clean
- [x] Lint: clean
- [x] Tests: 87/87 pass

## Decision
PASS — 1 warning logged, proceeding with commit.
```

## Quality Guidelines

> [!CAUTION]
> **BLOCKING STEP.** Phase 1 agents MUST be dispatched in a single message as parallel Task calls. Sequential dispatch (reviewer, then tester) defeats the purpose of the workflow — the gate must be fast to be used consistently.

> [!CAUTION]
> **BLOCKING STEP.** A `reviewer` Critical finding or any `tester` failure BLOCKS the commit. There are no exceptions — no "fix in follow-up" for Critical issues at commit time.

- MUST NOT: bypass the test gate with `--no-verify`. Fix the failing tests or document an explicit known-broken pre-existing failure.
- SHOULD: run `pnpm lint` (or repo equivalent) manually before invoking this workflow to avoid consuming reviewer context on style noise.
- SHOULD: for any staged change touching auth, secrets, or input validation, explicitly pass the diff to `security-auditor` in addition to `reviewer`.

## References

- `workflows/code-writing.md` — per-change reviewer gate during development (runs before this workflow)
- `workflows/plan-and-execute.md` — Phase 7 applies `code-writing.md` at phase boundaries, which leads here at commit time
- Agents: `reviewer`, `tester`

---
description: TDD feature development cycle. Tests written before implementation; no implementation starts without failing tests.
---

# /new-feature - New Feature

Code written without tests first is a commitment without a contract. Tests written after implementation tend to confirm what the code does rather than specify what it should do. This workflow enforces TDD: the `tester` agent defines the feature contract as failing tests before `coder` writes implementation. The implementation is then verified clean by a second `tester` pass. For UI features, `browser-qa-agent` confirms the feature in the actual browser context.

## When To Use

- Starting implementation of a new user-facing or API feature.
- Adding a new endpoint, component, service, or module that does not yet exist.
- Extending an existing feature with new behavior (if only fixing broken existing behavior, use `workflows/bug-fix.md`).
- Any task where the deliverable is new capability rather than restored correctness.

## Workflow

### Phase 1: Write Tests First

Dispatch `tester` with the full feature specification:

- Analyze the feature requirements
- Write failing tests that describe the expected behavior
- Cover: happy path, edge cases, error states, and (if relevant) authentication/authorization
- Confirm all new tests fail before handing off — a "passing" test before implementation means the test is not testing the right thing

Provide `tester` with: feature description, acceptance criteria, target file locations (if known), and existing patterns to match.

### Phase 2: Implement Feature

Dispatch the appropriate domain specialist with the feature requirements AND the test files from Phase 1:

- Default: `coder` for general implementation
- Route to `nextjs-developer` for Next.js App Router, RSC, or routing changes
- Route to `python-pro` for Python service or script implementation
- Route to other domain specialists as appropriate for the detected stack

Specialist responsibilities:

- Implement the feature following existing codebase patterns
- Make all new tests pass without modifying them
- Do not introduce new dependencies without explicit approval

Apply `workflows/code-writing.md` before committing: dispatch `reviewer` (and `security-auditor` if the feature touches auth, input validation, or data access).

### Phase 3: Verify

Dispatch `tester` (second pass):

- All new tests must pass
- All existing tests must pass (no regressions)
- Report any failures with file:line references

**Gate:** Zero failures before proceeding to Phase 4 or closing the feature.

### Phase 4: Browser QA (UI features only)

Dispatch `browser-qa-agent` if the feature has a browser-rendered UI:

- Navigate to the new feature
- Test all interactions defined in the feature specification
- Check for console errors
- Verify related features still work correctly

Skip this phase for: pure API features, library/utility code, database migrations, background jobs, CLI-only features.

## Quality Guidelines

> [!CAUTION]
> **BLOCKING STEP.** Tests MUST be written before implementation begins (TDD). If Phase 1 produces tests that all pass before Phase 2 runs, the tests are not testing the right thing. Stop and fix the test specification before dispatching `coder`.

> [!CAUTION]
> **BLOCKING STEP.** Phase 3 must show zero failures before the feature is committed. A feature that passes its own tests but breaks existing tests ships broken behavior.

- MUST: apply `workflows/code-writing.md` reviewer gate before committing the implementation.
- MUST: route to the correct domain specialist based on the detected stack — do not default to `coder` for framework-specific work.
- MUST NOT: introduce new external dependencies without explicit user approval.
- SHOULD: if Phase 1 reveals ambiguous requirements, surface them to the user before dispatching `coder`. Ambiguity discovered after implementation is more expensive to resolve.

## References

- `workflows/code-writing.md` — reviewer gate required at Phase 2 before commit
- `workflows/bug-fix.md` — use this instead if the task is restoring broken existing behavior
- `workflows/plan-and-execute.md` — if the feature spans multiple files or architectural layers, run this first
- Agents: `tester`, `coder`, `nextjs-developer`, `reviewer`, `security-auditor`, `browser-qa-agent`

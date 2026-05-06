---
description: Test-first bug fix cycle. Failing repro test required before any fix code is written.
---

# /bug-fix - Bug Fix

Fixing a bug without a failing test first is a guess. The test proves the bug exists and is reproducible; without it, "fixed" just means "the code changed." This workflow enforces the test-first contract: the `tester` agent must produce a failing reproduction test before `coder` writes a single line of fix code. The tester then verifies the fix. For UI bugs, `browser-qa-agent` confirms the fix in the actual browser context where the bug was reported.

## When To Use

- A bug has been reported or reproduced.
- A failing test exists but the root cause is unknown.
- A regression was introduced and needs to be isolated and fixed.
- Any code change whose purpose is to fix incorrect existing behavior (not add new behavior — use `workflows/new-feature.md` for that).

## Workflow

### Phase 1: Reproduce with Test

Dispatch `tester` with the full bug description:

- Create a test that fails and reproduces the bug exactly
- Test must target the specific failure mode, not a generalization
- The test should pass after the fix is applied (write it to describe correct behavior)
- Confirm the test fails before handing off

Provide `tester` with: bug description, steps to reproduce, expected vs. actual behavior, suspected file locations.

### Phase 2: Fix the Bug

Dispatch `coder` with the bug description AND the failing test file from Phase 1:

- Identify root cause (do not fix symptoms)
- Implement the minimal fix — do not refactor unrelated code
- Do not modify the test from Phase 1 unless it was incorrectly written

Apply `workflows/code-writing.md` before committing: dispatch `reviewer` (and `bug-auditor` if the fix touches error handling, null checks, or async paths).

### Phase 3: Verify

Dispatch `tester` (second pass):

- The new reproduction test must pass
- All existing tests must pass (no regressions)
- Report any test failures with file:line references

**Gate:** Zero failures before proceeding to Phase 4 or closing the fix.

### Phase 4: Browser QA (UI bugs only)

Dispatch `browser-qa-agent` if the bug was a UI or browser-rendered behavior:

- Reproduce the original steps from the bug report
- Confirm the bug is resolved
- Check that related features still work correctly

Skip this phase for: API bugs, background jobs, build/compilation issues, test infrastructure bugs, pure CLI behavior.

## Quality Guidelines

> [!CAUTION]
> **BLOCKING STEP.** A failing reproduction test MUST exist before any fix code is written. If Phase 1 cannot produce a failing test, escalate to the user — the bug may not be reproducible or the description may be incomplete. Do not proceed to Phase 2 with only a passing test or no test.

> [!CAUTION]
> **BLOCKING STEP.** Phase 3 must show zero failures before the fix is committed. A fix that passes the new test but breaks existing tests is not a fix — it is a regression swap.

- MUST: apply `workflows/code-writing.md` reviewer gate before committing the fix.
- MUST NOT: refactor unrelated code in the same commit as the fix. Scope is the bug and nothing else.
- SHOULD: if root cause analysis reveals a systemic issue (same bug pattern elsewhere), file a `bd create` issue for the broader fix rather than scope-creeping this one.

## References

- `workflows/code-writing.md` — reviewer gate required at Phase 2 before commit
- `workflows/new-feature.md` — if the "bug" turns out to be missing behavior, use this instead
- Agents: `tester`, `coder`, `reviewer`, `bug-auditor`, `browser-qa-agent`

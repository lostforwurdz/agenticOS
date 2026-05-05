---
description: Per-feature code change cycle. Code + tests written together, then independent review, then commit. NO commit without independent reviewer approval.
---

# /code-writing - Code Writing

Self-review misses what an independent agent catches in 30 seconds. The orchestrator that wrote or dispatched the code is pattern-blind to its own mistakes — that is the entire reason the reviewer gate exists. The gate is cheap insurance: one agent dispatch, fixed before commit, prevents the class of bugs that slip through every confident author's self-check.

## When To Use

- Any code change beyond a typo or a single-character fix.
- New feature implementation.
- Bug fix.
- Refactor (even if "no behavior change").
- Config change with runtime impact.
- Any change that will be committed to the repository.

## Workflow

### Phase 1: Write code AND tests concurrently

1. Write the implementation and the tests together. Do not write code first and tests after. Tests describe the expected behavior; the implementation satisfies them.
2. Use the `tester` agent or the repo's existing test framework. Match the test style and location conventions already in the repo.
3. If the change has no test surface (pure documentation, static config with no runtime impact), state this explicitly in the commit body. "No test surface: docs-only change" is a valid waiver. Silence is not.
4. Run the relevant tests locally before dispatching a reviewer. Do not waste a reviewer dispatch on tests that are already failing.

### Phase 2: Dispatch independent reviewer

1. Select the reviewer based on change type — dispatch multiple in parallel for combination changes:
   - General code correctness, logic, patterns → `reviewer` agent
   - Suspected runtime bugs, null refs, race conditions, edge cases → `bug-auditor` agent
   - Auth, secrets, input validation, OWASP surface, privilege escalation vectors → `security-auditor` agent
2. Provide the reviewer with:
   - File paths changed (absolute paths)
   - What changed and why (the intent, not a restatement of the diff)
   - Relevant context: related files, upstream callers, constraints from the plan file
   - The acceptance checklist from the plan file if one exists
3. The reviewer MUST be a different agent type than the one that wrote the code. If `coder` wrote it, `reviewer` reviews it. If `nextjs-developer` wrote it, `reviewer` or `bug-auditor` reviews it. The orchestrator reviewing its own dispatched work does NOT satisfy this gate.

### Phase 3: Address findings

1. Read the reviewer output. Triage findings:
   - **Critical**: fix before commit. No exceptions. Re-dispatch the same reviewer after fixing if the fix is non-trivial.
   - **Important**: fix before commit unless there is a documented reason to defer. If deferred, file a `bd create` issue immediately and note it in the commit body.
   - **Suggestions**: apply if in scope; otherwise file as `bd create` issues for follow-up. Do not block the commit on suggestions.
2. After applying Critical/Important fixes, re-run the tests (Phase 1 step 4) to confirm the fixes did not break anything.
3. If the reviewer flags Critical findings and fixes require significant rework, re-dispatch the reviewer on the revised code before proceeding to Phase 4.

### Phase 4: Run full test suite

1. Run the repo's full test gate:
   - JavaScript/TypeScript: `pnpm test` (or repo equivalent)
   - Python: `pytest` (or repo equivalent)
   - Rust: `cargo test`
   - Check `package.json`, `Makefile`, or CI config for the canonical command.
2. All tests must be green before committing. If a pre-existing test is failing and is unrelated to this change, document it in the commit body and file a `bd create` issue — do not let it block an unrelated commit silently.

### Phase 5: Commit at logical boundary

1. Prefer small atomic commits over one giant commit. One logical change per commit; if the feature required multiple distinct changes (e.g., schema + migration + UI), commit each separately.
2. For non-trivial commits, use the `git-manager` agent to write the commit message and, if this is going to a PR, the PR description.
3. The commit body MUST reference the reviewer that approved the change. Example:
   ```
   Reviewed-by: reviewer agent — clean (no findings)
   ```
   Or, if findings were addressed:
   ```
   Reviewed-by: bug-auditor — 2 Important findings addressed; 1 Suggestion filed as bd issue kobramaz-xyz
   ```
4. Do not use `--no-verify` or signing bypasses to make hooks pass. If a hook fails, investigate and fix the underlying issue.

## Quality Guidelines

> [!CAUTION]
> **BLOCKING STEP.** No commit lands without independent-reviewer approval. The agent (or orchestrator) that wrote or dispatched the code cannot be the reviewer. This is a hard gate — not a suggestion. Self-review does not satisfy it.

> [!CAUTION]
> If the reviewer flags Critical findings, fix and re-dispatch BEFORE committing. Do not "address in follow-up" for Critical findings. Important findings require either a fix or a filed `bd create` issue noted in the commit body.

- MUST: tests written alongside code, not after. The commit diff shows tests and implementation together.
- MUST: reviewer dispatch happens before `git commit`. Not after.
- MUST NOT: use `--no-verify` or `--no-gpg-sign` to skip hooks. Fix the hook or the code, not the gate.
- SHOULD: run `pnpm lint` (or repo equivalent) before dispatching the reviewer to avoid wasting reviewer context on style noise.
- SHOULD: for auth or secrets changes, always include `security-auditor` regardless of change size.

## References

- `workflows/plan-and-execute.md` — calls this workflow at every phase boundary during multi-step execution
- `workflows/session-close.md` — full test suite and push happen at close; this workflow gates the commit before that
- Agents: `reviewer`, `bug-auditor`, `security-auditor`, `tester`, `git-manager`

# Skills Audit — 2026-05-05

**No destructive action taken in this PR.** Each non-trivial recommendation is filed as a separate bd issue. Open `bd ready` to act on them individually.

**Summary:** 27 total entries (21 top-level files + 6 subdirs). 1 native, 6 partial, 12 boilerplate, 8 domain-helper.

**Recommendations breakdown:**
- keep: 8 (6 security subdirs + `gemini-router.md` + `nextjs.md`)
- rewrite-as-native: 4 (`code-review.md`, `compound-docs.md`, `debug.md`, `testing.md`)
- rewrite-as-workflow: 7 (`bug-fix.md`, `new-feature.md`, `pre-commit.md`, `pre-deploy.md`, `release-prep.md`, `full-audit.md`, `session-resume.md`)
- archive: 7 (`api-design.md`, `docker.md`, `mobile.md`, `performance.md`, `react-patterns.md`, `security.md`, `tailwind.md`)
- delete: 1 (`file-todos.md` — directly violates the no-TODO-files standing rule)

## Notable findings

The majority of the skills directory originated as imported boilerplate from another project (tracked in `docs/MACHINERY_DRIFT_REPORT.md` as the `atbfuture` migration). Roughly two-thirds of the 21 top-level files are imported with little or no adaptation: they reference paths (`todos/`, `compound-dashboard.sh`, `docs/solutions/`, `scripts/log-skill.sh`, `workflows/security-pass.md`, `references/common-errors.md`, `scripts/repro/`) that do not exist in this repository. The remaining third are intentional AgenticOS assets: `gemini-router.md` is the only fully native skill; `nextjs.md` is a clean domain reference relevant to active projects; and six security subdirs are clean Anthropic-authored imports that stand on their own.

The six security subdirs (`codeql/`, `differential-review/`, `insecure-defaults/`, `sarif-parsing/`, `semgrep/`, `supply-chain-risk-auditor/`) are self-contained and well-structured — they have no broken refs and are actively advertised in the system prompt as available skills. They should remain untouched. The `file-todos.md` skill is the most urgent item: it directly contradicts the "no markdown TODO lists" standing rule in `CLAUDE.md` and is cited by two archived workflows that would need updating before those workflows could be un-archived.

## Full audit table

| Skill | AgenticOS-native? | Status | Broken refs | Used by | Recommendation | Notes |
|-------|-------------------|--------|-------------|---------|----------------|-------|
| api-design.md | no | domain-helper | 0 | none | archive | Generic REST/GraphQL cheatsheet; no AgenticOS shape. Keep as topic ref. |
| bug-fix.md | partial | partial | 0 | none | rewrite-as-workflow | Sequential agent spawn pattern; already mirrored in `workflows/archived/bug-fix.md`. Belongs in `workflows/`. |
| code-review.md | no | boilerplate | 4 | README example, MACHINERY docs, `workflows/archived/review-compound.md` | rewrite-as-native | Refs `./scripts/log-skill.sh`, `workflows/security-pass.md`, `checklists/pre-merge.md`, `docs/solutions/patterns/`. Heavily referenced by `review-compound` so cannot delete; rewrite to point at `agents/reviewer.md` + `gemini-router` `strict-reviewer` flow. |
| compound-docs.md | no | boilerplate | 4 | `workflows/archived/work.md`, `workflows/archived/plan-compound.md`, `workflows/archived/review-compound.md` | rewrite-as-native | Whole "docs/solutions/" premise replaced by `bd remember`. Workflows still cite it. Rewrite as a thin pointer to `bd remember` conventions, OR delete and update three workflows. |
| debug.md | no | boilerplate | 4 | none | rewrite-as-native | Refs `workflows/reproduce-issue.md`, `templates/bug-report.template.md`, `references/common-errors.md`, `scripts/repro/` — none exist. Rewrite around `agents/debugger.md`. |
| docker.md | no | domain-helper | 0 | none | archive | Generic Dockerfile/compose snippets. Topic ref only. |
| file-todos.md | no | boilerplate | 2 | `workflows/archived/plan-compound.md`, `workflows/archived/work.md` | delete | Pure violation: refs `todos/`, contradicts the "no markdown TODO lists" rule in CLAUDE.md. Update workflow citations to `bd` and remove. |
| full-audit.md | partial | partial | 0 | none (mirror in `workflows/archived/`) | rewrite-as-workflow | Parallel-agent procedure already archived as `workflows/archived/full-audit.md`. Move to `workflows/` proper or delete the duplicate. |
| gemini-router.md | yes | native | 0 | `CLAUDE.md` line 44 | keep | Only fully AgenticOS-native skill. Clean. |
| mobile.md | no | domain-helper | 0 | none | archive | RN/Flutter cheatsheet. Topic ref. |
| new-feature.md | partial | partial | 0 | none (mirror in `workflows/archived/`) | rewrite-as-workflow | Sequential TDD agent procedure, not a skill. Already archived. |
| nextjs.md | partial | domain-helper | 0 | none | keep | Clean App Router patterns; relevant to `neighborhood_authority` project. Useful as topic ref. |
| performance.md | no | domain-helper | 0 | none | archive | Generic Core Web Vitals cheatsheet. |
| pre-commit.md | partial | partial | 0 | none (mirror in `workflows/archived/`) | rewrite-as-workflow | Two-step agent flow. Belongs in `workflows/`. |
| pre-deploy.md | partial | partial | 0 | none (mirror in `workflows/archived/`) | rewrite-as-workflow | Single-agent gate procedure. |
| react-patterns.md | no | domain-helper | 0 | none | archive | Generic hooks/composition cheatsheet. |
| release-prep.md | partial | partial | 0 | none (mirror in `workflows/archived/`) | rewrite-as-workflow | 6-phase sequential procedure. Classic workflow, not skill. |
| security.md | no | domain-helper | 0 | none | archive | Generic OWASP cheatsheet; superseded by the six security subdirs. |
| session-resume.md | no | boilerplate | 5 | none | rewrite-as-workflow | Refs `compound-dashboard.sh`, `todos/`, `plans/`, `.agent/workflows/`, `log-skill.sh`. Concept is now `workflows/session-start.md` (landing in this PR). Delete after this PR ships. |
| tailwind.md | no | domain-helper | 0 | none | archive | Generic v4 cheatsheet. |
| testing.md | no | boilerplate | 5 | none | rewrite-as-native | Refs placeholders, `log-skill.sh`, four nonexistent template/workflow paths. Rewrite as project-agnostic test-running skill or delete. |
| codeql/ | no | domain-helper | 0 | system prompt advertises as available skill | keep | Imported Anthropic security skill. Self-contained, well-structured. |
| differential-review/ | no | domain-helper | 0 | system prompt | keep | Imported Anthropic skill. Clean. |
| insecure-defaults/ | no | domain-helper | 0 | system prompt | keep | Imported Anthropic skill. Clean. |
| sarif-parsing/ | no | domain-helper | 0 | system prompt | keep | Imported Anthropic skill. Clean. |
| semgrep/ | no | domain-helper | 0 | system prompt | keep | Imported Anthropic skill. Clean. |
| supply-chain-risk-auditor/ | no | domain-helper | 0 | system prompt | keep | Imported Anthropic skill. Clean. |

## Cleanup sequence

1. Update workflows that cite `skills/file-todos/`, `skills/compound-docs/`, `skills/session-resume/` (those paths are wrong shape AND the targets are slated for delete/rewrite). All three referenced workflows are now in `workflows/archived/` so this cleanup unblocks any future un-archive.
2. Delete `file-todos.md` (violates standing rules).
3. Delete `session-resume.md` after this PR ships (superseded by `workflows/session-start.md`, which landed in this PR).
4. Move `bug-fix.md`, `new-feature.md`, `pre-commit.md`, `pre-deploy.md`, `release-prep.md`, `full-audit.md` to `workflows/`. Decide between the `skills/` and `workflows/archived/` versions per file.
5. Rewrite `code-review.md`, `compound-docs.md`, `debug.md`, `testing.md` as native (thin pointers to existing agents + `bd` patterns), or delete.
6. Add a top-of-file note to `nextjs.md`, `tailwind.md`, `react-patterns.md`, `api-design.md`, `docker.md`, `mobile.md`, `performance.md`, `security.md` flagging them as general topic references.
7. Leave six security subdirs and `gemini-router.md` untouched.

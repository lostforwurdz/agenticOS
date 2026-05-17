---
name: docs-sync
description: Reviews a git revision range after commits, identifies which documentation files (README, ARCHITECTURE.md, CLAUDE.md, docs/*, AGENTS.md, workflows/*, agents/*, loom-openapi.json) have drifted because of the code changes, applies precise updates, and gates the resulting docs commit through an independent reviewer subagent. Runs at session close before push. Default range = origin/main..HEAD.
model: sonnet
recommended_substrates: ["claude-code"]
---

# Docs Sync

## Required Skill

**MANDATORY:** Before claiming docs are synced, invoke `superpowers:verification-before-completion`. Read the files you claim to have updated. Every command in updated README sections must still be runnable. Every endpoint documented in `loom-openapi.json` must exist in `src/server.ts`. "Looks consistent" is not verification — quote the file:line of each thing you updated.

## When To Use

- At session close, after Phase 4 (persist non-obvious decisions) and before Phase 5 (push). Run against `git log origin/main..HEAD`.
- After a major commit during a session that materially changes a documented surface (new route, new table, new workflow, removed skill, etc.).
- (Future) Auto-fired by a post-commit git hook.

Do **not** run against an empty range. Do not run against ranges containing only doc-only commits (would loop on own work).

## Inputs

- **range** — git revision range (default: `origin/main..HEAD`). Caller can override with a specific commit SHA or wider range.
- **vault_root** — optional, for picking up `<vault>/context/WORKSPACE.md` updates when they exist.

## Workflow

### Phase 1 — Enumerate the change surface

1. Run `git log --oneline <range>` and `git diff --stat <range>`. Capture both.
2. Build a list of changed source files. Exclude pure doc files (`*.md` outside `agents/`, `loom-openapi.json`) from triggering self-update — those files were already updated by humans or other agents and don't drive doc drift by themselves.
3. If the changed-source list is empty after exclusion, write a one-line report stating "docs-sync: no source changes in range" and exit cleanly.

### Phase 2 — Classify drift surface

For each changed source file, identify which docs are at risk. Use this mapping (extend as needed; quote actual file:line you find):

| Source pattern | Likely doc impact |
|---|---|
| `src/db.ts` (new ALTER / CREATE TABLE) | README schema notes, `ARCHITECTURE.md`, `docs/vault-architecture.md` if vault-table, `docs/<feature>-architecture.md` if exists |
| `src/server.ts` (route registration changes) | `loom-openapi.json` (re-run `scripts/gen-openapi.ts`), any `docs/*-api.md` |
| `src/routes/*.ts` (handler signature changes) | OpenAPI spec, route-specific docs |
| `src/pool/adapters/*.ts` (new adapter, capability changes) | README adapter list, `ARCHITECTURE.md`, `CLAUDE.md` worker substrates table |
| `src/config.ts` (new config section) | README config example, `docs/*-config.md` |
| `src/vault/*.ts` (new vault behavior) | `docs/vault-architecture.md` |
| `src/evals/*.ts` (new eval surface) | `docs/evals.md` if exists; mention in README |
| `src/cli/*.ts` (new CLI command) | README CLI reference, `loom --help` output expectations |
| `workflows/*.md` (added/changed) | Constitution table in `CLAUDE.md`, cross-references in other workflows |
| `agents/*.md` (added/changed) | Constitution agents table, AGENTS.md cross-tool references, scheduled-agent table if applicable |
| `pipelines/*.json` (added/changed) | Pipelines table in `CLAUDE.md` / `~/loom/CLAUDE.md` |
| `scripts/*` (new scheduled / one-shot script) | README, `CLAUDE.md` install section, `scripts/install-*.sh` if applicable |
| `skills/*/SKILL.md` (added/changed) | Skill catalog docs, `CLAUDE.md` skills table |
| `src/pool/runner-middleware.ts` (new middleware) | README runner-middleware section, `CLAUDE.md` |
| `loom-openapi.json` schema mismatch | Always check that all routes in `src/server.ts` appear in the spec; flag drift even if no source change in this range (catches accumulated drift) |

If a changed source file fits a pattern not in this table, propose a new mapping in the report rather than silently skipping.

### Phase 3 — Read affected docs

For each doc identified in Phase 2:
1. Read the current content fully.
2. Identify the specific section(s) that reference the changed surface.
3. Compute the precise edit: what line(s) need to change, from what to what.
4. If the doc has no reference to the surface (the surface is undocumented), flag this as a drift (the change shipped to undocumented territory) — propose adding a new section or note rather than rewriting silently.

### Phase 4 — Apply edits

Apply the precise edits using Edit (preferred) or Write (only for new files). For OpenAPI spec drift, run `bun scripts/gen-openapi.ts` to regenerate `loom-openapi.json` rather than hand-editing.

**Edit rules:**
- Match existing voice and structure of the file you're editing.
- Do not reformat unchanged sections.
- Do not introduce new headings unless adding a genuinely new topic.
- Never reduce information (don't trim sections to make the diff smaller); only update what changed.
- Add a `<!-- updated <YYYY-MM-DD> from commit <sha> -->` comment where surgical updates are made to non-obvious sections, so future readers can trace the change.

### Phase 5 — Reviewer gate

Per the user's standing rule (no commit without reviewer approval, including docs commits):

1. Dispatch a `reviewer` subagent with the doc diff (`git diff --staged` after staging your edits).
2. Reviewer evaluates: are the edits factually correct? Do they actually reflect the source changes? Did you miss any docs that should have been updated?
3. On **approve**: proceed to Phase 6.
4. On **request changes**: apply the requested changes, re-stage, re-run reviewer once. If reviewer still rejects, abort the commit and write findings to `.claude/audits/AUDIT_DOCS_SYNC_<YYYY-MM-DD>.md` for human review.

### Phase 6 — Commit

```bash
git commit -m "docs: sync from <short-range-description>

Updated to reflect source changes in:
<bulleted list of source commits with one-line summaries>

Doc files touched:
<bulleted list with rationale per file>"
```

Do NOT push. The session-close workflow's Phase 5 handles pushing.

### Phase 7 — Surface unresolved deltas

If you identified doc drift but cannot fix it (e.g., requires user judgment, or surface is too undocumented to know what the correct doc should say), file a bd issue with a clear title and reference to the triggering commit. Do not stay silent.

## Output

Return a structured report:

1. **Range processed** — exact `git log` range
2. **Source files changed** — count + categorized list
3. **Docs identified as at-risk** — list with reason
4. **Docs actually updated** — list with file:line summary
5. **Docs flagged but not updated** — list with reason + bd issue links
6. **Reviewer verdict** — approve/request-changes/reject
7. **Commit SHA** — the docs commit (if Phase 6 ran)
8. **Anything deferred** — explicit unresolved items

## Constraints

- **Never modify code files.** Only documentation (.md, .json spec, .toml example fragments).
- **Never invent surface.** If unsure whether a code change requires a doc change, log and ask via bd issue rather than guessing.
- **Skip cleanly on empty/doc-only ranges.** Do not infinite-loop on own commits.
- **Honor the reviewer gate.** No exceptions to user's standing rule.
- **Quote file:line for every claim.** No "looks fine" — show the line.

## Failure modes to avoid

- **Stale OpenAPI spec.** This is the most common drift class — `src/server.ts` route additions don't auto-update `loom-openapi.json`. Always run `bun scripts/gen-openapi.ts` if any `src/server.ts` change is in range.
- **Documenting features that don't ship.** Just because a route exists doesn't mean it's reachable — verify via daemon if possible.
- **Adding hype text.** Doc updates should be terse and precise. No "exciting new feature" language.
- **Rewriting whole sections to fix one line.** Surgical edits only.
- **Skipping the reviewer.** No exceptions, even for "obviously safe" changes.

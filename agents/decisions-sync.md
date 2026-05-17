---
name: decisions-sync
description: Reviews the current session's chat transcript (~/.claude/projects/<project-id>/<session-uuid>.jsonl) for decisions the user made, captures each as "what + why + when + where" in bd remember under the decision.* namespace, so future sessions can search "why did we choose X" via bd memories. Runs at session close before docs-sync. Default: the most recent session JSONL for the current project.
model: sonnet
recommended_substrates: ["claude-code"]
---

# Decisions Sync

## Required Skill

**MANDATORY:** Before claiming decisions are captured, invoke `superpowers:verification-before-completion` via the Skill tool. For every decision you save to bd, quote the verbatim user turn it came from (file + line range in the JSONL). "I think the user wanted X" is not capture — show the quote.

## When To Use

- At session close, **Phase 4.4** (between Phase 4 memory persistence and Phase 4.5 docs-sync). The agent reads the current session's chat log and captures user decisions.
- Manually, when reviewing an old session for decisions that were never captured (`--session <uuid>` flag).

Do not run against an empty chat log. Do not duplicate decisions already stored in bd memory (check first).

## What counts as a decision

A **decision** is a user turn where the user picks one option over alternatives, sets a standing rule, defines a constraint, or signs off on an approach. Examples of decisions:

- **Selection between options:** "Go with #1 and #5", "Use Syncthing not Obsidian Sync", "All of them but in parallel"
- **Standing rules:** "I want a full review of every commit. No excuses.", "Any future trade-offs must be approved by the user"
- **Constraints:** "Don't add new npm deps", "Default to opt-in for security middleware"
- **Approval/rejection signals:** "Ship them", "Approve", "Inspect and make a decision", "Stop it"
- **Sequencing choices:** "Do FIXES first, then the roadmap", "Hold #3 in reserve"
- **Scope cuts:** "Out of scope for v1", "Defer that to a follow-up"
- **Preferences:** "I prefer terse responses", "Use bd not TodoWrite"

**NOT decisions (do not capture):**
- Questions the user asked ("what's next?")
- Status checks ("status?", "what's the state of X?")
- Acknowledgments ("ok", "thanks")
- Pure clarification requests ("what do you mean?")
- Tool output approvals (clicking through prompts) — unless the approval encodes a decision

A useful filter: if a future session would benefit from knowing **why** the user chose this path over alternatives, it's a decision. If it's only useful in the moment, it isn't.

## Inputs

- **session_jsonl** — path to the JSONL transcript. Default: most recent file in `~/.claude/projects/<project-id>/`. The project-id is the slugified working dir (e.g., `-home-kobramaz-loom` for `/home/kobramaz/loom`).
- **since** — optional timestamp filter; defaults to the start of the file.

## Workflow

### Phase 1 — Locate the session log

1. Resolve the current project's JSONL directory: `~/.claude/projects/<slugified-cwd>/`.
2. List files; pick the most recent `.jsonl` (largest mtime).
3. If no session log exists, write "decisions-sync: no session log found" and exit cleanly. Do not error.

### Phase 2 — Read and parse user turns

1. Read the JSONL file line by line.
2. Filter for user turns (`role: "user"` in the `message` field, or the harness equivalent). Skip tool result lines, system reminders, and assistant turns.
3. For each user turn, extract: timestamp, text content. Strip wrapping (e.g., `<user-prompt>` tags if present).
4. Keep a running line-range per turn for verbatim quoting later.

### Phase 3 — Identify decisions

For each user turn, classify against the decision criteria above. Be conservative — false positives bloat bd memory. When unsure, skip.

For each decision you identify:
- **WHAT** — the decision itself, in one sentence
- **WHY** — the reasoning, including alternatives considered. If the user's reasoning is implicit (e.g., they accepted your recommendation without explanation), state what was offered and which was chosen
- **WHEN** — ISO date + session UUID (last 8 chars) for traceability
- **WHERE** — file paths, bd ticket IDs, or surface names this decision affects, when applicable

### Phase 4 — Dedupe against existing bd memory

For each candidate decision, run `bd memories <keyword>` against 2–3 distinct keywords drawn from the WHAT field. If a prior `decision.*` entry already captures this decision, skip it (do not update existing — let the original stand unless it's flatly wrong, in which case file a bd issue and surface for user review).

### Phase 5 — Write to bd remember

For each new decision, store under the `decision.<YYYY-MM-DD>.<short-slug>` key pattern:

```bash
bd remember --key "decision.2026-05-16.no-skip-reviewer" "WHAT: Every commit gets an independent reviewer subagent before merge. No exceptions.
WHY: This session had multiple bugs (UI cost-fields, missing /evals/audit/runs route, OpenAPI drift) that an independent reviewer would have caught pre-commit. The orchestrator that wrote/dispatched code is pattern-blind to its own mistakes. Cost: 30 seconds per reviewer dispatch; benefit: avoids 15-minute outage cycles like the dashboard white-screen.
WHEN: 2026-05-16, session 5566749f
WHERE: workflows/code-writing.md (existing enforcement), all future Agent dispatches that produce commits.
QUOTE: 'I want a full review of every commit. No excuses. Any future trade-offs must be approved by the user.'"
```

The QUOTE field MUST be a verbatim copy of the user turn (or the relevant fragment) that the decision came from. This is the audit trail that lets future sessions confirm the decision wasn't paraphrased away.

### Phase 6 — Cross-link to code (when applicable)

If a decision affects specific code paths (e.g., "use /pool/costs not /pool/usage"), append a `WHERE` line listing the files. Future searches for "why did file X have shape Y" can then find the decision via grep on the WHERE field.

For decisions that govern bd tickets, append the ticket ID(s) — e.g., `WHERE: kobramaz-k9tq.11 (ExtractionMiddleware ticket)`.

### Phase 7 — Reviewer gate

Per the user's standing rule (every commit gets a reviewer; this agent produces bd memory writes, not git commits, but the principle applies to artifacts that influence future sessions):

1. Dispatch a `reviewer` subagent with the list of new bd entries you propose.
2. Reviewer checks: are the quotes verbatim? Is the WHY actually present in the source turn (not invented)? Are any candidates not actually decisions but acknowledgments / questions?
3. On **approve**: write the entries to bd via `bd remember --key ... "..."`.
4. On **request changes**: revise and re-submit once. If still rejected, write candidates to `.claude/audits/AUDIT_DECISIONS_SYNC_<YYYY-MM-DD>.md` and skip the bd writes.

### Phase 8 — Report

Return a structured summary:

1. **Session JSONL** — path + size + line count
2. **User turns** — count
3. **Decision candidates** — count
4. **Decisions deduped** — count (already in bd memory)
5. **Decisions written** — list of bd keys + WHAT one-liners
6. **Decisions deferred** — list of borderline cases the agent skipped, with reason
7. **Reviewer verdict** — approve / request-changes / reject

## Constraints

- **Quote verbatim.** No paraphrasing the user's words into "what I think they meant." The QUOTE field exists as the audit trail; if you can't quote it, you didn't capture it.
- **Be conservative.** False positives pollute bd memory. When unsure, skip and let a future session capture it manually.
- **Never modify existing decision entries.** If you find a conflict, file a bd issue rather than overwriting.
- **Honor the reviewer gate.** No exceptions.
- **Dedupe first.** Always `bd memories <keyword>` before writing. Don't recapture decisions from prior sessions.

## Output format example

```
decisions-sync: session 5566749f (47KB, 1247 lines, 89 user turns)
Decision candidates: 7
Already in bd memory: 2 (skipping)
Reviewer: approve (5/5)
Written:
  - decision.2026-05-16.no-skip-reviewer
  - decision.2026-05-16.parallel-default
  - decision.2026-05-16.session-close-docs-sync
  - decision.2026-05-16.recs-1-and-5
  - decision.2026-05-16.obsidian-via-syncthing
Deferred:
  - "status?" turn — pure status check, no decision
  - "Inspect and make a decision" — delegation, not a decision itself (captured what was delegated as a separate WHERE link)
```

## Failure modes to avoid

- **Capturing acknowledgments as decisions.** "ok", "yes", "approve" alone are not decisions — they're approvals of something previously proposed. If you capture them, capture the PROPOSED option as the WHAT and the approval as evidence in QUOTE.
- **Paraphrasing the quote.** The whole point of QUOTE is auditability. Verbatim only.
- **Recapturing prior-session decisions.** Always dedupe.
- **Writing decisions about agent behavior.** This agent captures user decisions, not its own. If the user said "do X", capture that; if the orchestrator decided to do Y in response, that's not a user decision.
- **Burying near-misses.** If a candidate is borderline, list it in "Deferred" with reasoning — let the user pull the trigger on capture if they want.

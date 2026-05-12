---
name: agent-hygiene-monthly
description: Scheduled agent - monthly read-only catalog scan of ~/agenticOS/agents/ that flags missing frontmatter, short descriptions, broken file references, and duplicate names, then writes a report to bd memory.
model: sonnet
---

# Agent Hygiene Monthly Agent

**Schedule:** 1st of each month 09:00 America/Chicago (`0 9 1 * *`)
**Scope:** All active agent prompt files in `~/agenticOS/agents/` (excluding `agents/archived/`).
**Venue:** Cloud routine (RemoteTrigger).

## Goal

Keep the agent catalog well-specified and internally consistent by catching structural defects — missing fields, broken path references, duplicate names, and weak descriptions — before they cause silent failures in the orchestrator or scheduled routines.

## Steps

1. **Enumerate agent files**

   List all `.md` files directly under `agents/`, excluding the `agents/archived/` subdirectory. Collect the full list as the working set for this run. Record total count.

2. **Parse frontmatter per agent**

   For each file, locate the frontmatter block delimited by `---` lines at the top. Extract fields: `name`, `description`, `model`. Flag any of the following:

   - Missing opening or closing `---` delimiter (malformed frontmatter)
   - `name` field absent or empty
   - `description` field absent or empty
   - `model` field absent or empty
   - `name` value does not match the filename (without `.md` extension) — case-sensitive comparison
   - `description` field value is shorter than 30 characters (likely a stub)

3. **Detect generic descriptions**

   For each description value, apply simple pattern matching to detect boilerplate phrasing. Flag descriptions that match patterns such as: starts with "does ", starts with "helps with ", is identical to another agent's description, or contains only one clause with no subject specificity. These are advisory flags, not errors.

4. **Detect duplicate name fields**

   Collect all `name:` values across the full working set. Flag any value that appears more than once, listing all files sharing that name.

5. **Verify cited file paths**

   Scan each agent file body (below the frontmatter) for path references matching these patterns:
   - `workflows/<anything>`
   - `scripts/<anything>`
   - `skills/<anything>`
   - `agents/<anything>`

   For each matched path, check whether the file exists relative to the `~/agenticOS/` repo root. Flag any path that does not resolve to an existing file. Do not validate URLs or external references.

6. **Compose and write report**

   Compute `TODAY` as ISO date at run time. Build a structured report:

   ```
   === AGENT HYGIENE REPORT <TODAY> ===
   Agents scanned: N
   Agents with frontmatter errors: K
   Agents with short/generic descriptions: L
   Duplicate name values: M
   Broken file references: P

   --- FRONTMATTER ERRORS ---
   <filename>: <specific issue>
   ...

   --- DESCRIPTION FLAGS (advisory) ---
   <filename>: <issue>
   ...

   --- DUPLICATE NAMES ---
   <name>: <file1>, <file2>
   ...

   --- BROKEN FILE REFERENCES ---
   <filename>: references <path> (not found)
   ...
   ```

   Write to bd:
   ```bash
   bd remember --key "agent-hygiene.<TODAY>" "<report>"
   ```

7. **File P2 bd issue if actionable defects found**

   If any agent has broken file references OR missing/malformed frontmatter, file one bd issue summarizing all affected agents:
   ```bash
   bd create --priority=2 --type=bug \
     --title="agent-hygiene: catalog defects found <TODAY>" \
     --description="<list of affected agents and issues>"
   ```
   Do not file separate issues per agent — one consolidated issue per monthly run is sufficient.

## Constraints

- Read-only — never modify any agent file
- Never auto-archive agents
- Never delete agents
- Do not scan `agents/archived/` — archived agents are intentionally not maintained
- Advisory description flags (generic phrasing) do not warrant a bd issue on their own; include them in the report text only
- Do not flag the reference file itself (`memory-consolidation.md`) for description style — it predates the current standard

## Verification

A successful run writes a bd memory key for today's date. Confirm with:
```bash
bd memories "agent-hygiene.$(date +%F)"
```
Output must be non-empty and must include the `=== AGENT HYGIENE REPORT ===` header. If actionable defects were found, an open P2 bd issue must exist titled `agent-hygiene: catalog defects found <TODAY>`.

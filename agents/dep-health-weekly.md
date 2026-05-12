---
name: dep-health-weekly
description: Scheduled agent - runs the /dep-health skill against active project repos every Monday and writes a consolidated summary to bd memory, filing P1 issues for critical findings.
model: sonnet
---

# Dependency Health Weekly Agent

**Schedule:** Mondays 09:00 America/Chicago (`0 9 * * 1`)
**Scope:** Active project repos: `loom`, `agenticOS`, `CMS_Next`. Cloud routine — repos must be listed as `git_repository` sources in the routine config.
**Venue:** Cloud routine (RemoteTrigger).

## Goal

Audit dependency health across all active repos once per week, surface critical findings as actionable bd issues, and persist a consolidated summary for trend tracking.

## Steps

1. **Resolve active project list**

   Use the hardcoded list: `loom`, `agenticOS`, `CMS_Next`. Each repo must be available as a cloned git repository in the routine's working environment via the `git_repository` source configuration. Confirm each repo directory is present before proceeding; skip and note any that are missing rather than failing the whole run.

2. **Run `/dep-health` per repo**

   For each available repo, invoke the `/dep-health` skill with that repo as scope. The skill fans out a dependency-manager agent, supply-chain-risk auditor, and compliance auditor in parallel, then consolidates via a debugger agent. Capture the full text output of each run as a per-repo report string.

3. **Classify findings**

   Parse each per-repo report for severity markers. Treat any finding labeled `CRITICAL` or `HIGH` (or equivalent top-severity language from the skill output) as a critical finding. Count totals per repo: critical, high, medium, low.

4. **Write consolidated summary to bd**

   Compute `TODAY` as the ISO date (`YYYY-MM-DD`) at run time. Write:
   ```bash
   bd remember --key "dep-health.weekly.<TODAY>" "<consolidated-summary>"
   ```
   The summary must include: run timestamp, repos checked, per-repo critical/high/medium/low counts, and a one-line verdict per repo (clean / advisory / action-required).

5. **File P1 bd issues for critical findings**

   For each repo that has at least one critical finding, file one bd issue per distinct critical finding:
   ```bash
   bd create --priority=1 --type=bug \
     --title="dep-health: <repo> <finding-summary>" \
     --description="<finding-details from skill output>"
   ```
   Do not batch multiple findings into a single issue — one issue per finding for clean tracking.

6. **Log completion**

   After all repos are processed, output a run summary to stdout listing repos processed, skipped, and total issues filed. This becomes the routine's run log.

## Constraints

- Report-only at the agent level — the `/dep-health` skill may file its own issues independently; do not suppress those
- Never auto-upgrade, auto-patch, or modify any dependency file
- Never commit, push, or open a PR
- Total runtime cap: 30 minutes; abort remaining repos if the cap is reached and note the abort in the bd summary
- Do not re-file an issue that already exists for the same repo + finding combination from this week's run

## Verification

A successful run writes a bd memory key matching `dep-health.weekly.<YYYY-MM-DD>` for today's date. Confirm with:
```bash
bd memories "dep-health.weekly.$(date +%F)"
```
Output must be non-empty. Any repo producing a critical finding must have a corresponding open P1 bd issue.

---
name: stale-branch-sweep
description: Scheduled agent - weekly report-only stale-branch audit across configured repos, classifying remote branches by age and merge status, writing a per-repo table to bd memory without deleting or modifying any branch.
model: sonnet
---

# Stale Branch Sweep Agent

**Schedule:** Fridays 08:00 America/Chicago (`0 8 * * 5`)
**Scope:** Configured repos: `loom`, `agenticOS`. Cloud routine — repos must be available as cloned git repositories in the routine environment.
**Venue:** Cloud routine (RemoteTrigger).

## Goal

Surface accumulated stale remote branches across active repos before the weekend, so the team can make deliberate pruning decisions during planned maintenance windows rather than discovering clutter during active development.

## Steps

1. **Fetch latest remote state per repo**

   For each configured repo (`loom`, `agenticOS`), confirm the repo directory is available. If a repo is missing, skip it and note the skip in the final report. For each available repo:
   ```bash
   git fetch --all --prune
   ```
   The `--prune` flag removes local refs for remote branches that have been deleted server-side; this prevents false positives from already-deleted branches.

2. **Enumerate remote branches and get last-commit timestamps**

   List all remote branches excluding `HEAD`:
   ```bash
   git branch -r | grep -v HEAD
   ```
   For each branch, retrieve the Unix timestamp of its last commit:
   ```bash
   git log -1 --format='%ct' origin/<branch>
   ```
   Also retrieve the author of that last commit:
   ```bash
   git log -1 --format='%an' origin/<branch>
   ```
   Compute age in days: `(NOW_UNIX - commit_unix) / 86400`. Flag any branch with age >= 30 days as stale.

3. **Classify stale branches**

   For each stale branch, determine merge status against `main`:
   ```bash
   git branch -r --merged origin/main | grep "origin/<branch>"
   ```
   - If the branch appears in the merged list: classify as **merged** (safe to delete, but do not delete)
   - If the branch does not appear: classify as **abandoned** (unmerged work, requires human review before any action)

   Special cases: branches named `audit/*` (from `full-audit-weekly`) that are older than 60 days and are merged are classified as **merged-audit-artifact**.

4. **Compose per-repo report table**

   For each repo, build a Markdown table:

   ```
   ### <repo> — stale branches (>= 30 days)

   | Branch | Age (days) | Classification | Last Author |
   |--------|-----------|----------------|-------------|
   | feature/old-thing | 47 | abandoned | dev@example.com |
   | fix/merged-patch | 35 | merged | dev@example.com |
   ```

   Include a summary line: total remote branches, total stale, merged vs. abandoned breakdown.

5. **Write consolidated report to bd**

   Compute `TODAY` as ISO date at run time:
   ```bash
   bd remember --key "stale-branches.<TODAY>" "<report>"
   ```
   The report must include all per-repo tables and a global summary (total branches across repos, total stale, total merged, total abandoned).

6. **File P3 bd issues for repos with excessive stale branch counts**

   If any single repo has more than 5 stale branches, file one P3 bd issue for that repo:
   ```bash
   bd create --priority=3 --type=task \
     --title="stale-branches: <repo> has <N> stale branches as of <TODAY>" \
     --description="<per-repo table from step 4>"
   ```
   One issue per repo per weekly run. Do not file if the count is 5 or fewer.

## Constraints

- NEVER delete, prune, merge, or modify any branch — report only
- NEVER push to any repo
- NEVER force-push under any circumstances
- `git fetch --all --prune` is the only write-like operation permitted; it only updates local ref tracking, not remote state
- Do not flag branches named `main`, `master`, `develop`, or `staging` as stale regardless of age
- Do not flag branches that were created by the `full-audit-weekly` agent in the last 7 days

## Verification

A successful run writes a bd memory key for today's date. Confirm with:
```bash
bd memories "stale-branches.$(date +%F)"
```
Output must be non-empty and must include at least one `###` repo heading. Any repo with more than 5 stale branches must have an open P3 bd issue.

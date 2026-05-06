---
name: content-pr
description: >-
  Sequential gate for content PRs (marketing pages, blog posts, SEO surfaces).
  Runs seo-auditor → ui-auditor → accessibility-tester → reviewer in order;
  each phase blocks the next. Any Critical finding halts the chain. Invoke
  when a PR is labeled "content" or when the diff touches marketing/blog/mdx
  content. Produces per-phase audit reports and a final reviewer sign-off.
---

# Content PR Gate

Sequential four-phase review for content PRs. Each phase gates the next; a Critical finding halts the chain until resolved.

## Trigger

Invoke when a PR carries the `content` label, or the diff touches `app/(marketing)/`, `app/blog/`, or any `*.mdx` file.

## Phases (sequential — wait for each to complete before dispatching the next)

**Phase 1 — SEO Audit:** dispatch `seo-auditor` agent. Checks: meta tags, structured data (JSON-LD), sitemap, OpenGraph, Lighthouse SEO score. Output → `.claude/audits/CONTENT_seo_<timestamp>.md`.

> [!CAUTION]
> **BLOCKING STEP.** Critical finding from any phase: halt, fix, re-run before continuing to the next phase.

**Phase 2 — UI Audit:** dispatch `ui-auditor` agent with diff + Phase 1 report. Checks: design pattern consistency, layout regressions. Output → `.claude/audits/CONTENT_ui_<timestamp>.md`.

**Phase 3 — Accessibility:** dispatch `accessibility-tester` agent with diff + Phase 1–2 reports. Checks: WCAG 2.1 AA, keyboard navigation, color contrast. Output → `.claude/audits/CONTENT_accessibility_<timestamp>.md`.

**Phase 4 — Final Review:** dispatch `reviewer` agent with diff + all three phase reports. Provides final sign-off. Output → `.claude/audits/CONTENT_reviewer_<timestamp>.md`.

## Verification

- [ ] All four `.claude/audits/CONTENT_<phase>_<timestamp>.md` files exist.
- [ ] `reviewer` phase report contains explicit approval sign-off.
- [ ] No unresolved Critical findings across any phase.

## References

- `workflows/plan-and-execute.md` — use this skill as Phase 7 gate for content-focused plan phases

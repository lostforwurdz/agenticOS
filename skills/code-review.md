---
name: code-review
description: Pointer to the registered `superpowers:requesting-code-review` skill — invoke that when completing work to request structured pre-merge review.
---

# code-review

This skill is a pointer. Use the registered `superpowers:requesting-code-review` skill for actual review work; it guides you to request review at the right checkpoints (task completion, major features, pre-merge) and verifies the work meets requirements.

For PR-shaped reviews invoke `superpowers:requesting-code-review`. For pre-merge gating with parallel reviewer + tester dispatch, see `workflows/pre-commit.md`. For incoming feedback on a review you've received, see `superpowers:receiving-code-review`.

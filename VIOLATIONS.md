# Violations Log

**Read this before your first action every session.**

Each entry: what rule was broken, what concretely happened, what to do instead.
Add a new entry whenever a rule is violated or the user corrects your approach.

---

## 2026-04-18 — Problem-fit check before building

**Rule:** Understand what problem you are actually solving before producing artifacts.

**What happened:** User asked for "a memory system." I found a research paper on Adaptive Memory Replay (AMR) for continual learning of neural networks, read it deeply, and produced a full 7-task implementation plan with PyTorch training loops, loss functions, and bandit algorithms — before asking what the user wanted to build. The plan was entirely wrong. The user wanted persistent cross-session memory for Claude, not a training-time algorithm for updating model weights. I wasted a plan and the user's time.

**What to do instead:** Before writing any plan or producing any artifact, ask one clarifying question: "What outcome are you trying to achieve?" Do not assume the stated input (a paper, a library, a keyword) IS the goal. One question costs 10 seconds. A wrong plan costs an hour.

---

## 2026-04-18 — Skill invocation before responding

**Rule:** If there is even a 1% chance a skill applies, invoke it before any response — including clarifying questions.

**What happened:** Throughout sessions I rationalize around skill invocation with thoughts like "this is just a conversation," "I need more context first," or "this doesn't need a formal skill." These are explicitly listed as red flags in the using-superpowers skill and I still do it.

**What to do instead:** When any of these thoughts appear, that is the signal to stop and invoke the skill. The red flag thoughts ARE the trigger.

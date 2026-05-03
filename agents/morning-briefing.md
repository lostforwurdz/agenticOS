---
name: morning-briefing
description: Scheduled weekday morning agent — pulls bd ready, episodic memory, and any connected calendar/email/issue-tracker MCPs into a prioritized daily plan. Degrades gracefully when optional integrations are not connected.
model: sonnet
---

# Morning Briefing Agent

**Schedule:** Weekdays 8:00 AM local (`0 8 * * 1-5`)
**Scope:** anywhere with the agenticOS repo and beads. Platform-agnostic.

## Goal

Give a focused, scannable daily plan in under 30 seconds of reading.

## Steps

1. **Required: beads ready queue**
   ```bash
   bd ready
   ```
   Top issues sorted by readiness, priority, and due date. This is the floor — always works, no external auth needed.

2. **Required: due / overdue check**
   ```bash
   bd query "SELECT id, title, due, priority FROM issues WHERE status='open' AND due IS NOT NULL AND due <= date('now','+1 day') ORDER BY due"
   ```
   Surfaces anything due today or already past-due.

3. **Optional: episodic memory recap**
   - If the `episodic-memory:search-conversations` agent is available, query for unresolved threads from the last 48h.
   - Skip silently if not available.

4. **Optional: connected calendar / email / issues MCPs**
   - Check `claude mcp list` for available MCPs. For each, pull what's relevant:
     - Google Calendar MCP → today's events
     - Gmail MCP → unread threads from last 24h, subject lines only
     - Linear MCP → assigned issues + mentions
     - Slack MCP → urgent DMs / thread mentions
   - **If any of these is configured but disconnected, surface that as actionable** (e.g., "Re-auth Linear MCP to enable inbox section").
   - **If none of these are available**, skip those sections entirely — do not fabricate.

5. **Synthesize**
   - Calendar (if available): what's time-boxed
   - Inbox (if available): urgent or actionable
   - Issues (if available): top 3
   - Beads: top 3 from `bd ready` + anything due/overdue
   - Cross-cut: what one thing matters most today

6. **Save plan summary**
   ```bash
   bd remember --key "plan.daily_$(date +%Y-%m-%d)" "<summary>"
   ```

7. **Output to user**

## Output format

```
## Morning Briefing — {date}

### Schedule
{events from calendar, or "(no calendar MCP connected)"}

### Inbox
{urgent threads, or "(no email MCP connected)"}

### Issues
{top 3 from external trackers, or "(no issue tracker MCP connected)"}

### Beads
- Due/overdue: {bd query result}
- Top ready: {bd ready top 3}

### Focus
{1-2 sentence synthesis of what matters most today}

### Reauth needed (if any)
{list any configured-but-disconnected MCPs}
```

## Constraints

- Always render the **Beads** section — that's the agent's core value
- Never fabricate calendar events, emails, or issues from MCPs that aren't connected
- Be terse: scannable in under 30 seconds
- Use absolute dates ("2026-05-04") not relative ("tomorrow") in saved memory
- Platform-agnostic — no hardcoded paths to specific machines or operating systems

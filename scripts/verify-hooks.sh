#!/usr/bin/env bash
# verify-hooks.sh — static verification of AgenticOS hook wiring.
# Confirms settings.json contains the expected hooks and that all
# their dependencies resolve. Does NOT (cannot) verify the hooks
# actually fire from a running session — that requires restarting
# Claude Code; manual verification steps printed at the end.
set -uo pipefail

CLAUDE="${HOME}/.claude"
SETTINGS="$CLAUDE/settings.json"
PASS=0
FAIL=0

ok()   { echo "  ok    $*"; PASS=$((PASS+1)); }
fail() { echo "  FAIL  $*"; FAIL=$((FAIL+1)); }

echo "=== AgenticOS hook verification ==="
echo "Settings file: $SETTINGS"
echo

if [[ ! -f "$SETTINGS" ]]; then
  fail "settings.json not found"
  exit 2
fi

if ! python3 -c "import json; json.load(open('$SETTINGS'))" 2>/dev/null; then
  fail "settings.json is not valid JSON"
  exit 2
fi
ok "settings.json is valid JSON"

# 1. Check PreToolUse[EnterPlanMode] -> agent: violations-enforcer
HOOK1=$(python3 -c "
import json
s = json.load(open('$SETTINGS'))
hooks = s.get('hooks', {}).get('PreToolUse', [])
for entry in hooks:
    if entry.get('matcher') == 'EnterPlanMode':
        for h in entry.get('hooks', []):
            if h.get('type') == 'agent' and h.get('agent') == 'violations-enforcer':
                print('found'); break
        else: continue
        break
" 2>/dev/null)
if [[ "$HOOK1" == "found" ]]; then
  ok "PreToolUse[EnterPlanMode] -> agent: violations-enforcer"
else
  fail "PreToolUse[EnterPlanMode] -> violations-enforcer NOT wired"
fi

# 2. Check SessionStart -> command: bd prime
HOOK2=$(python3 -c "
import json
s = json.load(open('$SETTINGS'))
hooks = s.get('hooks', {}).get('SessionStart', [])
for entry in hooks:
    for h in entry.get('hooks', []):
        if h.get('type') == 'command' and h.get('command') == 'bd prime':
            print('found'); break
    else: continue
    break
" 2>/dev/null)
if [[ "$HOOK2" == "found" ]]; then
  ok "SessionStart -> command: bd prime"
else
  fail "SessionStart -> bd prime NOT wired"
fi

# 3. Confirm violations-enforcer agent file exists and has valid frontmatter
AGENT="$CLAUDE/agents/violations-enforcer.md"
if [[ ! -f "$AGENT" ]]; then
  fail "agent file missing: $AGENT"
else
  ok "agent file present: $AGENT"
  if ! head -1 "$AGENT" | grep -q '^---$'; then
    fail "agent file frontmatter looks malformed (no leading '---')"
  else
    ok "agent file frontmatter starts correctly"
  fi
fi

# 4. Confirm bd prime command works
if command -v bd >/dev/null 2>&1; then
  if bd prime >/dev/null 2>&1; then
    ok "'bd prime' executes cleanly"
  else
    fail "'bd prime' exists but errored"
  fi
else
  fail "'bd' not in PATH"
fi

# 5. Confirm VIOLATIONS.md exists (the agent reads it)
VIOL="$CLAUDE/VIOLATIONS.md"
if [[ -f "$VIOL" || -L "$VIOL" ]]; then
  ok "VIOLATIONS.md present (the violations-enforcer agent reads this)"
else
  fail "VIOLATIONS.md missing — violations-enforcer will report 'no violations file found'"
fi

echo
echo "=== Static verification ==="
echo "  passed: $PASS"
echo "  failed: $FAIL"

if [[ $FAIL -gt 0 ]]; then
  echo
  echo "Static checks failed. Fix above issues before relying on the hooks."
  exit 1
fi

cat <<'EOF'

=== Static state OK. Now verify the hooks actually fire ===

Static checks confirm the hooks are wired correctly, but they cannot
prove they fire — that requires restarting Claude Code (hooks load at
session start). To verify after a fresh Claude Code session:

  1. SessionStart hook (bd prime):
     - Start a new Claude Code session.
     - Ask the agent any beads-related question (e.g., "what bd commands
       can I run?"). It should respond with detailed bd workflow context
       it would not have without 'bd prime' being injected — meaning it
       will reference the SESSION CLOSE PROTOCOL, dolt push, etc.
     - Or check session telemetry/transcript for evidence the bd prime
       output was added to the prompt.

  2. PreToolUse[EnterPlanMode] hook (violations-enforcer agent):
     - In a fresh session, ask for a non-trivial plan ("plan a refactor
       of X that touches Y files").
     - The orchestrator should call EnterPlanMode. Just before the plan
       dialog appears, you should see violations-enforcer output —
       either matching VIOLATIONS.md entries or "no matches — proceed."
     - If you see plan mode open without that intermediate output, the
       hook is not firing.

If either hook fails the live test, check ~/.claude/settings.json
backup files (.bak-pre-hooks-wire, .bak-pre-sessionstart-hook) and
restart Claude Code after restoring.
EOF

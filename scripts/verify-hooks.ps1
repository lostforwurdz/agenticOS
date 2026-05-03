# verify-hooks.ps1 — static verification of AgenticOS hook wiring on Windows.
# Confirms settings.json contains the expected hooks and that all
# their dependencies resolve. Does NOT (cannot) verify the hooks
# actually fire from a running session — that requires restarting
# Claude Code; manual verification steps printed at the end.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File verify-hooks.ps1
#
# Exits 0 if all static checks pass, 1 if any fail, 2 if settings.json
# is missing or unparseable.

$ErrorActionPreference = "Continue"

$Claude   = Join-Path $env:USERPROFILE ".claude"
$Settings = Join-Path $Claude "settings.json"
$Pass = 0
$Fail = 0

function Ok   { param([string]$Msg); Write-Host "  ok    $Msg"; $script:Pass++ }
function Fail { param([string]$Msg); Write-Host "  FAIL  $Msg" -ForegroundColor Red; $script:Fail++ }

Write-Host "=== AgenticOS hook verification ==="
Write-Host "Settings file: $Settings"
Write-Host ""

if (-not (Test-Path $Settings)) {
    Fail "settings.json not found"
    exit 2
}

try {
    $cfg = Get-Content -Raw -Path $Settings | ConvertFrom-Json
    Ok "settings.json is valid JSON"
} catch {
    Fail "settings.json is not valid JSON: $_"
    exit 2
}

# 1. PreToolUse[EnterPlanMode] -> agent: violations-enforcer
$found = $false
foreach ($entry in @($cfg.hooks.PreToolUse)) {
    if ($entry.matcher -eq "EnterPlanMode") {
        foreach ($h in @($entry.hooks)) {
            if ($h.type -eq "agent" -and $h.agent -eq "violations-enforcer") {
                $found = $true; break
            }
        }
        if ($found) { break }
    }
}
if ($found) {
    Ok "PreToolUse[EnterPlanMode] -> agent: violations-enforcer"
} else {
    Fail "PreToolUse[EnterPlanMode] -> violations-enforcer NOT wired"
}

# 2. SessionStart -> command: bd prime
$found = $false
foreach ($entry in @($cfg.hooks.SessionStart)) {
    foreach ($h in @($entry.hooks)) {
        if ($h.type -eq "command" -and $h.command -eq "bd prime") {
            $found = $true; break
        }
    }
    if ($found) { break }
}
if ($found) {
    Ok "SessionStart -> command: bd prime"
} else {
    Fail "SessionStart -> bd prime NOT wired"
}

# 3. violations-enforcer agent file
$Agent = Join-Path $Claude "agents\violations-enforcer.md"
if (-not (Test-Path $Agent)) {
    Fail "agent file missing: $Agent"
} else {
    Ok "agent file present: $Agent"
    $firstLine = Get-Content -Path $Agent -TotalCount 1
    if ($firstLine -ne "---") {
        Fail "agent file frontmatter looks malformed (no leading '---')"
    } else {
        Ok "agent file frontmatter starts correctly"
    }
}

# 4. bd prime works
$bd = Get-Command bd -ErrorAction SilentlyContinue
if (-not $bd) {
    Fail "'bd' not in PATH"
} else {
    & bd prime *> $null
    if ($LASTEXITCODE -eq 0) {
        Ok "'bd prime' executes cleanly"
    } else {
        Fail "'bd prime' exists but errored (exit $LASTEXITCODE)"
    }
}

# 5. VIOLATIONS.md present (real file or symlink)
$Viol = Join-Path $Claude "VIOLATIONS.md"
if (Test-Path $Viol) {
    Ok "VIOLATIONS.md present (the violations-enforcer agent reads this)"
} else {
    Fail "VIOLATIONS.md missing — violations-enforcer will report 'no violations file found'"
}

Write-Host ""
Write-Host "=== Static verification ==="
Write-Host "  passed: $Pass"
Write-Host "  failed: $Fail"

if ($Fail -gt 0) {
    Write-Host ""
    Write-Host "Static checks failed. Fix above issues before relying on the hooks." -ForegroundColor Red
    exit 1
}

@"

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

If either hook fails the live test, check %USERPROFILE%\.claude\settings.json
backup files and restart Claude Code after restoring.
"@

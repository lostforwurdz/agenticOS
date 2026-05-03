# install-windows.ps1 — symlink %USERPROFILE%\.claude\* and %USERPROFILE%\.gemini\skills
# into the agenticOS repo on Windows.
#
# Requirements:
#   - Windows 10 build 14972+ (2017 or newer)
#   - "Developer Mode" enabled, OR run this script as Administrator
#       Settings -> Privacy & security -> For developers -> Developer Mode = ON
#   - The repo cloned at $env:USERPROFILE\agenticOS
#
# Idempotent: safe to re-run. Replaces existing symlinks. Backs up real files.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File install-windows.ps1
#   # or after Set-ExecutionPolicy -Scope CurrentUser RemoteSigned:
#   .\install-windows.ps1

param(
    [string]$RepoPath = (Join-Path $env:USERPROFILE "agenticOS")
)

$ErrorActionPreference = "Stop"

$Claude = Join-Path $env:USERPROFILE ".claude"
$Gemini = Join-Path $env:USERPROFILE ".gemini"
$Stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $Claude "_pre-symlink-backup-$Stamp"

if (-not (Test-Path $RepoPath)) {
    Write-Host "ERROR: $RepoPath not found." -ForegroundColor Red
    Write-Host "Clone first: git clone https://github.com/lostforwurdz/agenticOS.git `"$RepoPath`""
    exit 1
}

# Pre-flight: confirm symlink creation will succeed
$DevMode = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -ErrorAction SilentlyContinue).AllowDevelopmentWithoutDevLicense
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (($DevMode -ne 1) -and (-not $IsAdmin)) {
    Write-Host "ERROR: Symlink creation requires Developer Mode OR Administrator." -ForegroundColor Red
    Write-Host "Either:"
    Write-Host "  1. Settings -> Privacy & security -> For developers -> Developer Mode = ON, then re-run this script"
    Write-Host "  2. Re-run as Administrator"
    exit 1
}

New-Item -ItemType Directory -Force -Path $Claude, $Gemini | Out-Null

function MakeSafeLink {
    param([string]$Target, [string]$LinkPath)

    if (Test-Path -LiteralPath $LinkPath) {
        $item = Get-Item -LiteralPath $LinkPath -Force
        if ($item.LinkType -eq "SymbolicLink") {
            # $item.Target is a string[] in PS5+, scalar in earlier; -contains handles both.
            if ($item.Target -contains $Target) {
                Write-Host "  ok     $LinkPath -> $Target"
                return
            }
            Remove-Item -LiteralPath $LinkPath -Force
        } else {
            New-Item -ItemType Directory -Force -Path $Backup | Out-Null
            $dest = Join-Path $Backup (Split-Path $LinkPath -Leaf)
            Move-Item -LiteralPath $LinkPath -Destination $dest -Force
            Write-Host "  backup $LinkPath -> $dest"
        }
    }

    New-Item -ItemType SymbolicLink -Force -Path $LinkPath -Target $Target | Out-Null
    Write-Host "  link   $LinkPath -> $Target"
}

Write-Host "=== AgenticOS install (Windows) ==="
Write-Host "Repo:   $RepoPath"
Write-Host "Claude: $Claude"
Write-Host "Gemini: $Gemini"
Write-Host ""

MakeSafeLink (Join-Path $RepoPath "CLAUDE.md")     (Join-Path $Claude "CLAUDE.md")
MakeSafeLink (Join-Path $RepoPath "AGENTS.md")     (Join-Path $Claude "AGENTS.md")
MakeSafeLink (Join-Path $RepoPath "VIOLATIONS.md") (Join-Path $Claude "VIOLATIONS.md")
MakeSafeLink (Join-Path $RepoPath "agents")        (Join-Path $Claude "agents")
MakeSafeLink (Join-Path $RepoPath "skills")        (Join-Path $Claude "skills")
MakeSafeLink (Join-Path $RepoPath "workflows")     (Join-Path $Claude "workflows")
MakeSafeLink (Join-Path $RepoPath "gemini\skills") (Join-Path $Gemini "skills")

Write-Host ""
if (Test-Path $Backup) {
    Write-Host "Backups saved to: $Backup"
}

Write-Host ""
Write-Host "Verifying with claude mcp list..."
if (Get-Command claude -ErrorAction SilentlyContinue) {
    claude mcp list
} else {
    Write-Host "  claude CLI not in PATH; install Claude Code first"
}

Write-Host ""
Write-Host "Done. Edit `$env:USERPROFILE\.claude\CLAUDE.md and changes land in $RepoPath."

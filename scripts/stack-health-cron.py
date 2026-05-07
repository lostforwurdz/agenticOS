#!/usr/bin/env python3
"""stack-health-cron.py — nightly scheduled wrapper around stack-health.py.

Runs the probe, persists the result to bd remember, and auto-files a bd issue
when the stack is red on consecutive nights.

Schedule:
- Linux: systemd user timer at 23:30 (see scripts/systemd/stack-health.{service,timer})
- Windows: Task Scheduler at 23:30 (registration command at bottom of this file)

Behavior per run:
1. Invoke `stack-health.py --json --quick`. Capture stdout, parse JSON.
2. Persist full JSON to `bd remember --key "stack-health.YYYY-MM-DD"`.
3. Append one-line summary to ~/.local/state/agenticos/stack-health.log
   (Linux) or %LOCALAPPDATA%\\agenticos\\stack-health.log (Windows).
4. If today's run has any red layer AND yesterday's persisted result also
   had any red layer AND no open bd issue with title prefix "stack-health
   red" exists, create one with the layer names + dates.

Idempotency: only one open bd issue at a time per "outage." Once that
issue closes and a new consecutive-red event happens, a fresh issue is
filed.

Exit codes:
0 — probe ran (regardless of probe result)
1 — probe couldn't run at all (missing stack-health.py, etc.)
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timedelta, timezone


HOME = pathlib.Path.home()
STACK_HEALTH_PROBE = HOME / "agenticOS/scripts/stack-health.py"


def _log_dir() -> pathlib.Path:
    if sys.platform == "win32":
        base = pathlib.Path(os.environ.get("LOCALAPPDATA", HOME / "AppData/Local"))
        return base / "agenticos"
    return HOME / ".local/state/agenticos"


LOG_FILE = _log_dir() / "stack-health.log"


def _resolve_bd() -> str:
    """Resolve bd to a path that bypasses the npm .CMD shim on Windows.

    cmd.exe re-tokenizes args containing characters like 'OK:' or quotes,
    breaking `bd remember "<long json>"`. We bypass the .CMD by finding
    the underlying bd.exe directly.

    bd's specific shim calls `node + bd.js` (which then spawns bd.exe as
    a grandchild). The .exe sits at:
      <npm_dir>/node_modules/@beads/bd/bin/bd.exe

    Strategy: shutil.which("bd"), check for sibling node_modules/@beads/
    bin/bd.exe; fall back to .CMD if not present.
    """
    import shutil

    resolved = shutil.which("bd")
    if resolved is None:
        raise RuntimeError("bd not on PATH")
    if sys.platform != "win32":
        return resolved
    # npm-installed location (covers both .cmd and bare wrappers)
    candidate = (
        pathlib.Path(resolved).parent
        / "node_modules" / "@beads" / "bd" / "bin" / "bd.exe"
    )
    if candidate.exists():
        return str(candidate)
    return resolved


def _bd_run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run bd with utf-8 forced + .CMD shim bypass on Windows."""
    bd_path = _resolve_bd()
    return subprocess.run(
        [bd_path, *cmd],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        check=False,
    )


def run_probe() -> dict:
    """Invoke stack-health.py --json --quick and parse the response.

    Returns the parsed JSON dict. Raises RuntimeError if probe can't run.
    """
    if not STACK_HEALTH_PROBE.exists():
        raise RuntimeError(f"probe not found at {STACK_HEALTH_PROBE}")
    r = subprocess.run(
        [sys.executable, str(STACK_HEALTH_PROBE), "--json", "--quick"],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        check=False, timeout=120,
    )
    if not r.stdout.strip():
        raise RuntimeError(f"probe emitted no stdout (exit {r.returncode}, stderr: {r.stderr[:200]})")
    return json.loads(r.stdout)


def persist_result(report: dict) -> str:
    """Save the report to bd remember. Returns the key used."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"stack-health.{today}"
    payload = json.dumps(report, separators=(",", ":"))
    r = _bd_run(["remember", "--key", key, payload])
    if r.returncode != 0:
        raise RuntimeError(f"bd remember failed: {r.stderr[:200]}")
    return key


def append_log(report: dict) -> None:
    """One-line summary to a log file for quick chronological review."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    s = report.get("summary", {})
    line = (
        f"{report.get('generated_at', '?')} "
        f"host={report.get('host', '?')} "
        f"green={s.get('green', 0)} yellow={s.get('yellow', 0)} "
        f"red={s.get('red', 0)} skipped={s.get('skipped', 0)}\n"
    )
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def red_layers(report: dict) -> list[str]:
    return [r["name"] for r in report.get("results", []) if r.get("status") == "red"]


def fetch_yesterday_report() -> dict | None:
    """Fetch yesterday's stack-health.YYYY-MM-DD memory if it exists."""
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime("%Y-%m-%d")
    key = f"stack-health.{yesterday}"
    r = _bd_run(["memories", key, "--json"])
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        wrap = json.loads(r.stdout)
        # bd memories returns {key: value} with the value being our serialized JSON string
        inner = wrap.get(key)
        if not isinstance(inner, str):
            return None
        return json.loads(inner)
    except json.JSONDecodeError:
        return None


def existing_open_issue() -> str | None:
    """Return id of any open bd issue with title prefix 'stack-health red',
    or None if none exists. Idempotency guard for auto-filing."""
    r = _bd_run(["list", "--status=open", "--json"])
    if r.returncode != 0:
        return None
    try:
        items = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None
    for item in items:
        if item.get("title", "").lower().startswith("stack-health red"):
            return item.get("id")
    return None


def file_issue(today_red: list[str], yesterday_red: list[str]) -> str:
    """Create a bd issue summarizing the consecutive-red event. Returns id."""
    union = sorted(set(today_red) | set(yesterday_red))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime("%Y-%m-%d")
    title = f"stack-health red 2+ nights: {', '.join(union)}"
    description = (
        f"Auto-filed by stack-health-cron 2026-{today}. The memory stack has "
        f"reported red layers on consecutive nights:\n\n"
        f"- {yesterday}: red = {sorted(yesterday_red)}\n"
        f"- {today}: red = {sorted(today_red)}\n\n"
        f"Recovery procedure: `~/agenticOS/workflows/memory-stack-recovery.md` "
        f"covers each layer. Run `python ~/agenticOS/scripts/stack-health.py` "
        f"manually to see the current state."
    )
    r = _bd_run([
        "create",
        "--title", title,
        "--description", description,
        "--type=bug",
        "--priority=1",
    ])
    if r.returncode != 0:
        raise RuntimeError(f"bd create failed: {r.stderr[:200]}")
    # Parse out the issue id from "✓ Created issue: <id> — <title>"
    for line in r.stdout.splitlines():
        if "Created issue:" in line:
            parts = line.split("Created issue:", 1)[1].strip().split()
            if parts:
                return parts[0]
    return "<unknown>"


def main() -> int:
    try:
        report = run_probe()
    except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        print(f"stack-health-cron: probe failed: {e}", file=sys.stderr)
        return 1

    try:
        key = persist_result(report)
        append_log(report)
        print(f"stack-health-cron: persisted {key}", file=sys.stderr)
    except RuntimeError as e:
        print(f"stack-health-cron: persist failed: {e}", file=sys.stderr)
        # Continue — still try to surface red state via stderr below

    today_red = red_layers(report)
    if not today_red:
        return 0

    print(f"stack-health-cron: red layers today: {today_red}", file=sys.stderr)
    yesterday_report = fetch_yesterday_report()
    if yesterday_report is None:
        print("stack-health-cron: no yesterday data; not filing yet", file=sys.stderr)
        return 0
    yesterday_red = red_layers(yesterday_report)
    if not yesterday_red:
        print("stack-health-cron: yesterday was green; not filing yet", file=sys.stderr)
        return 0

    open_issue = existing_open_issue()
    if open_issue:
        print(f"stack-health-cron: existing open issue {open_issue}; skipping file", file=sys.stderr)
        return 0

    issue_id = file_issue(today_red, yesterday_red)
    print(f"stack-health-cron: filed bd issue {issue_id}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())


# -----------------------------------------------------------------------------
# Windows Task Scheduler registration (run once interactively)
# -----------------------------------------------------------------------------
#
# $script = "$env:USERPROFILE\agenticOS\scripts\stack-health-cron.py"
# $py = (Get-Command python).Source
# $action = New-ScheduledTaskAction -Execute $py -Argument "`"$script`""
# $trigger = New-ScheduledTaskTrigger -Daily -At 11:30PM
# $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
# Register-ScheduledTask -TaskName "stack-health-cron" `
#     -Action $action -Trigger $trigger -Settings $settings `
#     -Description "Nightly memory-stack health probe + auto-bd-issue"
#
# Verify:  Get-ScheduledTask stack-health-cron | Get-ScheduledTaskInfo
# Disable: Disable-ScheduledTask -TaskName stack-health-cron
# Run now: Start-ScheduledTask -TaskName stack-health-cron

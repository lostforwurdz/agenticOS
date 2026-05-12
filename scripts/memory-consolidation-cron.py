#!/usr/bin/env python3
"""memory-consolidation-cron.py — nightly scheduled wrapper around the memory-consolidation agent.

Reads the agent prompt from agents/memory-consolidation.md, invokes claude -p headlessly,
persists the report to bd remember, and exits.

Schedule:
- Linux: systemd user timer at 23:00 (see scripts/systemd/memory-consolidation.{service,timer})

Behavior per run:
1. Read ~/agenticOS/agents/memory-consolidation.md as the prompt.
2. Invoke `claude -p --permission-mode plan` with that prompt. Capture stdout.
3. Persist full report to `bd remember --key "memory-consolidation.report.<hostname>.<YYYY-MM-DD>"`.

Exit codes:
0 — agent ran and report was persisted
1 — agent couldn't run or persist failed
"""
from __future__ import annotations

import os
import pathlib
import socket
import subprocess
import sys
from datetime import datetime, timezone


HOME = pathlib.Path.home()
AGENT_PROMPT_FILE = HOME / "agenticOS/agents/memory-consolidation.md"

CLAUDE_TIMEOUT = 300  # 5 minutes


def _resolve_bd() -> str:
    """Resolve bd to a path that bypasses the npm .CMD shim on Windows."""
    import glob
    import shutil

    resolved = shutil.which("bd")
    if resolved is None:
        # systemd-user services inherit a minimal PATH that excludes nvm/npm-global;
        # probe common install locations before giving up.
        candidates = [
            *glob.glob(str(pathlib.Path.home() / ".nvm/versions/node/*/bin/bd")),
            str(pathlib.Path.home() / ".npm-global/bin/bd"),
            "/usr/local/bin/bd",
        ]
        for c in candidates:
            if pathlib.Path(c).exists():
                resolved = c
                break
    if resolved is None:
        raise RuntimeError("bd not on PATH")
    if sys.platform != "win32":
        return resolved
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
    # bd has `#!/usr/bin/env node`; under systemd-user the inherited PATH lacks
    # nvm's bin dir, so prepend bd's parent so the sibling `node` resolves too.
    env = os.environ.copy()
    bd_parent = str(pathlib.Path(bd_path).parent)
    if bd_parent not in env.get("PATH", "").split(os.pathsep):
        env["PATH"] = bd_parent + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [bd_path, *cmd],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        check=False, env=env,
    )


def read_prompt() -> str:
    if not AGENT_PROMPT_FILE.exists():
        raise RuntimeError(f"agent prompt not found at {AGENT_PROMPT_FILE}")
    return AGENT_PROMPT_FILE.read_text(encoding="utf-8")


def run_agent(prompt: str) -> str:
    """Invoke claude -p headlessly with the given prompt. Returns stdout."""
    import shutil

    claude_bin = shutil.which("claude")
    if claude_bin is None:
        raise RuntimeError("claude not on PATH")
    # Pass prompt via stdin to avoid argv quoting issues when the prompt body
    # starts with `---` (frontmatter) or contains other CLI-flag-looking chars.
    r = subprocess.run(
        [claude_bin, "-p", "--permission-mode", "plan"],
        input=prompt,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        check=False, timeout=CLAUDE_TIMEOUT,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"claude exited {r.returncode}; stderr: {r.stderr[:200]}"
        )
    return r.stdout


def persist_report(report: str) -> str:
    """Persist the report to bd remember. Returns the key used."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    hostname = socket.gethostname()
    key = f"memory-consolidation.report.{hostname}.{today}"
    r = _bd_run(["remember", "--key", key, report])
    if r.returncode != 0:
        raise RuntimeError(f"bd remember failed: {r.stderr[:200]}")
    return key


def main() -> int:
    try:
        prompt = read_prompt()
    except RuntimeError as e:
        print(f"memory-consolidation-cron: prompt read failed: {e}", file=sys.stderr)
        return 1

    print("memory-consolidation-cron: invoking claude agent", file=sys.stderr)
    try:
        report = run_agent(prompt)
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"memory-consolidation-cron: agent failed: {e}", file=sys.stderr)
        return 1

    try:
        key = persist_report(report)
        print(f"memory-consolidation-cron: persisted {key}", file=sys.stderr)
    except RuntimeError as e:
        print(f"memory-consolidation-cron: persist failed: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

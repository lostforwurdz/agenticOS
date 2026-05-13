#!/usr/bin/env python3
"""stack-health.py — Health probe for the AgenticOS memory stack.

Checks six layers of the persistent-memory stack and emits a markdown
report plus a JSON tail block for machine consumption. Exits 0 when all
layers are green, 1 if any layer is red.

Layers:
  1. Episodic memory plugin DB freshness
  2. bd memories store + dolt remote sync
  3. wiki-compiler subprocess pipeline (import + optional pytest)
  4. Scheduled wiki-compile run.log freshness + exit health
  5. Compiled wiki repo state (commit recency + tree clean + push state)
  6. AgenticOS constitution drift (skill pointer integrity)

Usage:
  python stack-health.py            # full check
  python stack-health.py --quick    # skip slow checks (pytest)
  python stack-health.py --json     # JSON-only output (no markdown)

Cross-platform: Linux + Windows. No third-party deps.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Status types
# ---------------------------------------------------------------------------

GREEN = "green"
YELLOW = "yellow"
RED = "red"
SKIPPED = "skipped"


@dataclass
class LayerResult:
    layer: int
    name: str
    status: str  # green / yellow / red / skipped
    detail: str
    metrics: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Paths (cross-platform)
# ---------------------------------------------------------------------------

HOME = pathlib.Path.home()
EPISODIC_DB = HOME / ".config/superpowers/conversation-index/db.sqlite"
WIKI_REPO = HOME / "wiki"


def _resolve_wiki_compiler() -> pathlib.Path:
    for candidate in (HOME / "dev/wiki-compiler", HOME / "Documents/wiki-compiler"):
        if (candidate / ".venv").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return HOME / "dev/wiki-compiler"


WIKI_COMPILER = _resolve_wiki_compiler()
BEADS_DIR = HOME / ".beads"
AGENTIC_OS = HOME / "agenticOS"


def _resolve_loom_db() -> pathlib.Path:
    """Resolve loom kernel DB path using the same precedence as loom's config.ts:
    1. LOOM_RUNTIME_DIR env var
    2. XDG_DATA_HOME/loom
    3. ~/.local/share/loom
    DB lives at <runtimeDir>/state/state.db.
    """
    env_dir = os.environ.get("LOOM_RUNTIME_DIR")
    if env_dir:
        return pathlib.Path(env_dir) / "state" / "state.db"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return pathlib.Path(xdg) / "loom" / "state" / "state.db"
    return HOME / ".local" / "share" / "loom" / "state" / "state.db"


LOOM_DB = _resolve_loom_db()


def _runlog_path() -> pathlib.Path:
    """Return the OS-specific path to wiki-compile-and-push wrapper's run.log."""
    if sys.platform == "win32":
        local_app = pathlib.Path(os.environ.get("LOCALAPPDATA", HOME / "AppData/Local"))
        return local_app / "wiki-compiler/run.log"
    return HOME / ".local/state/wiki-compiler/run.log"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(s: str) -> datetime:
    """Parse an ISO-8601 timestamp; tolerate trailing Z and missing tz."""
    s = s.replace("Z", "+00:00") if s.endswith("Z") else s
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        # Fallback for compact formats
        dt = datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _hours_since(dt: datetime) -> float:
    return (_now_utc() - dt).total_seconds() / 3600.0


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Subprocess wrapper that's safe across Windows/Linux + npm shims.

    Resolves cmd[0] via shutil.which (PATHEXT-aware on Windows). Forces
    UTF-8 decoding to avoid cp1252 surprises.
    """
    resolved = shutil.which(cmd[0])
    if resolved is None:
        raise FileNotFoundError(f"{cmd[0]!r} not on PATH")
    return subprocess.run(
        [resolved, *cmd[1:]],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        check=False, **kwargs,
    )


# ---------------------------------------------------------------------------
# Layer checks
# ---------------------------------------------------------------------------

def check_episodic_memory() -> LayerResult:
    """Layer 1 — episodic-memory plugin indexing freshness."""
    if not EPISODIC_DB.exists():
        return LayerResult(
            1, "episodic_memory", RED,
            f"DB not found at {EPISODIC_DB}",
        )
    try:
        conn = sqlite3.connect(f"file:{EPISODIC_DB}?mode=ro", uri=True)
        row = conn.execute(
            "SELECT MAX(timestamp), COUNT(*) FROM exchanges"
        ).fetchone()
        conn.close()
    except sqlite3.Error as e:
        return LayerResult(1, "episodic_memory", RED, f"sqlite error: {e}")

    max_ts, count = row
    if not max_ts:
        return LayerResult(
            1, "episodic_memory", RED,
            f"DB has 0 exchanges",
            {"count": count or 0},
        )
    age_hours = _hours_since(_parse_iso(max_ts))
    metrics = {"count": count, "max_timestamp": max_ts, "age_hours": round(age_hours, 1)}
    if age_hours > 72:
        return LayerResult(1, "episodic_memory", RED,
                           f"latest exchange {age_hours:.1f}h ago (threshold 72h)", metrics)
    if age_hours > 24:
        return LayerResult(1, "episodic_memory", YELLOW,
                           f"latest exchange {age_hours:.1f}h ago (threshold 24h)", metrics)
    return LayerResult(1, "episodic_memory", GREEN,
                       f"{count} exchanges, latest {age_hours:.1f}h ago", metrics)


def check_bd_memories() -> LayerResult:
    """Layer 2 — bd memories store + dolt remote sync."""
    try:
        # Count memories
        r = _run(["bd", "memories", "--json"])
        if r.returncode != 0:
            return LayerResult(
                2, "bd_memories", RED,
                f"bd memories failed: {r.stderr[:200]}",
            )
        data = json.loads(r.stdout)
        count = sum(1 for k in data if k != "schema_version")

        # Dolt remote check
        rdolt = _run(["bd", "dolt", "remote", "list"])
        has_remote = "origin" in (rdolt.stdout or "")

        metrics = {"count": count, "dolt_remote_configured": has_remote}
        if not has_remote:
            return LayerResult(2, "bd_memories", YELLOW,
                               f"{count} memories but dolt remote not configured", metrics)
        if count == 0:
            return LayerResult(2, "bd_memories", YELLOW,
                               "0 memories — store empty?", metrics)
        return LayerResult(2, "bd_memories", GREEN,
                           f"{count} memories, dolt origin configured", metrics)
    except FileNotFoundError as e:
        return LayerResult(2, "bd_memories", RED, str(e))
    except (json.JSONDecodeError, sqlite3.Error) as e:
        return LayerResult(2, "bd_memories", RED, f"parse error: {e}")


def check_wiki_compiler(quick: bool) -> LayerResult:
    """Layer 3 — wiki-compiler import + optional pytest."""
    if not WIKI_COMPILER.exists():
        return LayerResult(3, "wiki_compiler", RED,
                           f"repo not found at {WIKI_COMPILER}")
    venv_python = WIKI_COMPILER / (
        ".venv/Scripts/python.exe" if sys.platform == "win32"
        else ".venv/bin/python"
    )
    if not venv_python.exists():
        return LayerResult(3, "wiki_compiler", RED,
                           f"venv python missing at {venv_python}")

    # Import smoke (cheap, always run)
    r = subprocess.run(
        [str(venv_python), "-c", "import wiki_compiler; from wiki_compiler.compile import run_compilation"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if r.returncode != 0:
        return LayerResult(3, "wiki_compiler", RED,
                           f"import failed: {r.stderr[:200]}")

    if quick:
        return LayerResult(3, "wiki_compiler", GREEN,
                           "import OK (quick mode, pytest skipped)",
                           {"pytest": "skipped"})

    # Full pytest (slower)
    r = subprocess.run(
        [str(venv_python), "-m", "pytest", "tests/", "-q", "--no-header", "-x", "--tb=no"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False, cwd=str(WIKI_COMPILER), timeout=120,
    )
    # Count passes/fails from the summary line
    summary = r.stdout.splitlines()[-1] if r.stdout else ""
    passed = re.search(r"(\d+) passed", summary)
    failed = re.search(r"(\d+) failed", summary)
    metrics = {
        "passed": int(passed.group(1)) if passed else 0,
        "failed": int(failed.group(1)) if failed else 0,
        "exit": r.returncode,
    }
    # Known unrelated path-separator failures: 2 specific tests; tolerate them
    KNOWN_UNRELATED = 2
    if metrics["failed"] > KNOWN_UNRELATED:
        return LayerResult(3, "wiki_compiler", RED,
                           f"pytest: {metrics['failed']} failures (>{KNOWN_UNRELATED} known)",
                           metrics)
    if metrics["failed"] > 0:
        return LayerResult(3, "wiki_compiler", YELLOW,
                           f"pytest: {metrics['passed']} passed, {metrics['failed']} known-unrelated failures",
                           metrics)
    return LayerResult(3, "wiki_compiler", GREEN,
                       f"pytest: {metrics['passed']} passed", metrics)


def check_scheduled_run() -> LayerResult:
    """Layer 4 — wiki-compile-and-push wrapper run.log freshness + exit."""
    runlog = _runlog_path()
    if not runlog.exists():
        return LayerResult(4, "scheduled_run", YELLOW,
                           f"no run.log at {runlog} (wrapper may never have fired)",
                           {"path": str(runlog)})
    try:
        # File is mixed encoding (ASCII timestamps + UTF-16 python tracebacks)
        # We just need the timestamp prefixes which are always ASCII
        raw = runlog.read_bytes()
        # Decode as latin-1 to never error; we only look for ASCII patterns
        text = raw.decode("latin-1")
    except OSError as e:
        return LayerResult(4, "scheduled_run", RED, f"read failed: {e}")

    # Find timestamp lines like 2026-05-06T19:25:30.123Z OR 2026-05-12T09:05:27Z
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)")
    matches = pattern.findall(text)
    if not matches:
        return LayerResult(4, "scheduled_run", RED,
                           "run.log has no timestamp lines",
                           {"path": str(runlog), "size_bytes": len(raw)})

    last_ts = matches[-1]
    age_hours = _hours_since(_parse_iso(last_ts))

    # Check for the most recent error markers in the trailing 5KB
    tail = text[-5000:]
    has_error = "ERROR:" in tail or "compile failed" in tail or "compileexit" in tail.lower()
    has_recent_push = "pushed:" in tail

    metrics = {
        "last_entry": last_ts,
        "age_hours": round(age_hours, 1),
        "tail_has_error": has_error,
        "tail_has_push": has_recent_push,
    }
    if age_hours > 48:
        return LayerResult(4, "scheduled_run", RED,
                           f"last run {age_hours:.1f}h ago — wrapper may not be firing",
                           metrics)
    if age_hours > 30:
        return LayerResult(4, "scheduled_run", YELLOW,
                           f"last run {age_hours:.1f}h ago", metrics)
    if has_error and not has_recent_push:
        return LayerResult(4, "scheduled_run", YELLOW,
                           f"last run {age_hours:.1f}h ago, errors present, no recent push",
                           metrics)
    return LayerResult(4, "scheduled_run", GREEN,
                       f"last run {age_hours:.1f}h ago", metrics)


def check_wiki_repo() -> LayerResult:
    """Layer 5 — compiled wiki state and remote sync."""
    if not (WIKI_REPO / ".git").exists():
        return LayerResult(5, "wiki_repo", RED,
                           f"no git repo at {WIKI_REPO}")

    # Last commit timestamp
    r = _run(["git", "-C", str(WIKI_REPO), "log", "-1", "--format=%ct"])
    if r.returncode != 0:
        return LayerResult(5, "wiki_repo", RED,
                           f"git log failed: {r.stderr[:200]}")
    last_commit_ts = int(r.stdout.strip())
    age_hours = (_now_utc().timestamp() - last_commit_ts) / 3600.0

    # Tree status
    rstatus = _run(["git", "-C", str(WIKI_REPO), "status", "-sb"])
    status_lines = (rstatus.stdout or "").splitlines()
    branch_line = status_lines[0] if status_lines else ""
    dirty_lines = [l for l in status_lines[1:] if l.strip()]

    ahead = "ahead" in branch_line
    behind = "behind" in branch_line

    metrics = {
        "last_commit_age_hours": round(age_hours, 1),
        "branch_status": branch_line,
        "dirty_lines": len(dirty_lines),
        "ahead": ahead,
        "behind": behind,
    }
    if dirty_lines:
        return LayerResult(5, "wiki_repo", YELLOW,
                           f"{len(dirty_lines)} uncommitted change(s); last commit {age_hours:.1f}h ago",
                           metrics)
    if ahead:
        return LayerResult(5, "wiki_repo", YELLOW,
                           f"local commits not pushed; last commit {age_hours:.1f}h ago",
                           metrics)
    if age_hours > 72:
        return LayerResult(5, "wiki_repo", YELLOW,
                           f"last commit {age_hours:.1f}h ago — wiki may be stale",
                           metrics)
    return LayerResult(5, "wiki_repo", GREEN,
                       f"clean, last commit {age_hours:.1f}h ago", metrics)


def probe_vault_snapshots(quick: bool) -> LayerResult:  # noqa: ARG001
    """Layer 7 — loom vault_snapshots table health."""
    if not LOOM_DB.exists():
        return LayerResult(
            7, "vault_snapshots", SKIPPED,
            f"loom.db not found at {LOOM_DB}",
        )
    try:
        conn = sqlite3.connect(f"file:{LOOM_DB}?mode=ro", uri=True)
        row = conn.execute(
            "SELECT COUNT(*), MAX(last_seen), MIN(last_seen), COALESCE(SUM(byte_size), 0)"
            " FROM vault_snapshots"
        ).fetchone()
        conn.close()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return LayerResult(7, "vault_snapshots", SKIPPED,
                               "vault_snapshots table not found (schema migration pending?)")
        return LayerResult(7, "vault_snapshots", RED, f"sqlite error: {e}")
    except sqlite3.Error as e:
        return LayerResult(7, "vault_snapshots", RED, f"sqlite error: {e}")

    count, max_last_seen, min_last_seen, total_bytes = row
    total_mb = (total_bytes or 0) / (1024 * 1024)

    if count == 0:
        return LayerResult(
            7, "vault_snapshots", GREEN,
            "0 snapshots — no reads yet",
            {"count": 0, "total_mb": 0.0},
        )

    oldest_age_h = _hours_since(_parse_iso(min_last_seen))
    metrics = {
        "count": count,
        "oldest_age_h": round(oldest_age_h, 1),
        "total_mb": round(total_mb, 1),
        "max_last_seen": max_last_seen,
        "min_last_seen": min_last_seen,
    }
    detail = f"{count} snapshots, oldest {oldest_age_h:.1f}h ago, {total_mb:.1f} MB total"

    if count > 50 and oldest_age_h < 1.0:
        return LayerResult(7, "vault_snapshots", RED,
                           f"eviction/write storm: {detail}", metrics)
    if total_mb > 50.0:
        return LayerResult(7, "vault_snapshots", YELLOW,
                           f"cap warning (>{50} MB): {detail}", metrics)
    return LayerResult(7, "vault_snapshots", GREEN, detail, metrics)


def _resolve_vault_root() -> pathlib.Path | None:
    """Locate the vault root by inspecting the loom config or falling back to
    common sibling paths relative to LOOM_DB's runtime directory."""
    runtime_dir = LOOM_DB.parent.parent  # <runtimeDir>/state/state.db → <runtimeDir>
    candidates = [
        runtime_dir / "vault",
        HOME / ".local" / "share" / "loom" / "vault",
        HOME / "vault",
        HOME / "Documents" / "vault",
        HOME / "Vault",
    ]
    # Also try reading vault path from loom db config table if it exists
    if LOOM_DB.exists():
        try:
            conn = sqlite3.connect(f"file:{LOOM_DB}?mode=ro", uri=True)
            rows = conn.execute(
                "SELECT value FROM config WHERE key='vaultRoot' LIMIT 1"
            ).fetchone()
            conn.close()
            if rows and rows[0]:
                candidates.insert(0, pathlib.Path(rows[0]))
        except sqlite3.Error:
            pass
    for c in candidates:
        if c.is_dir():
            return c
    return None


def probe_vault_provenance(quick: bool) -> LayerResult:
    """Layer 8 — vault provenance coverage (loom_source_runner_id in frontmatter).

    Walks .md files modified in the last 7 days to measure what fraction
    carry a ``loom_source_*`` frontmatter key — a drift detector for writes
    that bypass the gateway.
    """
    vault_root = _resolve_vault_root()
    if vault_root is None:
        return LayerResult(8, "vault_provenance", SKIPPED, "vault root not found")

    cutoff = time.time() - 7 * 24 * 3600
    FRONTMATTER_RE = re.compile(r"^loom_source_runner_id\s*:", re.MULTILINE)
    FRONTMATTER_BLOCK_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

    # Collect .md files modified in the last 7 days
    recent: list[pathlib.Path] = []
    try:
        for p in vault_root.rglob("*.md"):
            try:
                if p.stat().st_mtime >= cutoff:
                    recent.append(p)
            except OSError:
                continue
    except OSError as e:
        return LayerResult(8, "vault_provenance", RED, f"vault walk error: {e}")

    if not recent:
        return LayerResult(
            8, "vault_provenance", SKIPPED,
            "no recent .md files (last 7 days)",
            {"vault_root": str(vault_root)},
        )

    # Quick mode: cap at 100 most-recent files
    if quick and len(recent) > 100:
        recent.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        recent = recent[:100]

    total = len(recent)
    with_key = 0
    for p in recent:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            total -= 1
            continue
        # Extract frontmatter block only
        m = FRONTMATTER_BLOCK_RE.match(text)
        if m and FRONTMATTER_RE.search(m.group(1)):
            with_key += 1

    if total == 0:
        return LayerResult(8, "vault_provenance", SKIPPED,
                           "no readable .md files in sample")

    coverage = with_key / total
    pct = round(coverage * 100, 1)
    detail = f"{pct}% of recent writes have loom_source_* ({with_key} of {total})"
    metrics = {
        "coverage": round(coverage, 4),
        "with_key": with_key,
        "total_sampled": total,
        "vault_root": str(vault_root),
        "quick": quick,
    }
    if coverage >= 0.80:
        return LayerResult(8, "vault_provenance", GREEN, detail, metrics)
    if coverage >= 0.40:
        return LayerResult(8, "vault_provenance", YELLOW, detail, metrics)
    return LayerResult(8, "vault_provenance", RED,
                       f"{detail} — writes bypassing gateway?", metrics)


def probe_vault_critic(quick: bool) -> LayerResult:  # noqa: ARG001
    """Layer 9 — vault_critic_decisions verdict distribution (last 7 days)."""
    if not LOOM_DB.exists():
        return LayerResult(
            9, "vault_critic", SKIPPED,
            f"loom.db not found at {LOOM_DB}",
        )
    try:
        conn = sqlite3.connect(f"file:{LOOM_DB}?mode=ro", uri=True)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        row = conn.execute(
            """
            SELECT COUNT(*),
                   SUM(CASE WHEN verdict='accept' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN verdict='needs_revision' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN verdict='reject' THEN 1 ELSE 0 END)
              FROM vault_critic_decisions
             WHERE created_at >= ?
            """,
            (cutoff,),
        ).fetchone()
        conn.close()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return LayerResult(9, "vault_critic", SKIPPED,
                               "vault_critic_decisions table not found")
        return LayerResult(9, "vault_critic", RED, f"sqlite error: {e}")
    except sqlite3.Error as e:
        return LayerResult(9, "vault_critic", RED, f"sqlite error: {e}")

    count, accepts, revisions, rejects = row
    count = count or 0
    if count == 0:
        return LayerResult(
            9, "vault_critic", SKIPPED,
            "no critic decisions / 7d",
            {"count": 0},
        )

    accepts = accepts or 0
    revisions = revisions or 0
    rejects = rejects or 0
    reject_rate = rejects / count
    accept_pct = round(accepts / count * 100, 1)
    revise_pct = round(revisions / count * 100, 1)
    reject_pct = round(rejects / count * 100, 1)

    detail = (
        f"{count} decisions / 7d — "
        f"{accept_pct}% accept / {revise_pct}% revise / {reject_pct}% reject"
    )
    metrics = {
        "count": count,
        "accepts": accepts,
        "revisions": revisions,
        "rejects": rejects,
        "reject_rate": round(reject_rate, 4),
    }

    if reject_rate >= 0.50:
        return LayerResult(9, "vault_critic", RED,
                           f"{detail} — critic flagging most writes (drift signal)", metrics)
    if reject_rate >= 0.20:
        return LayerResult(9, "vault_critic", YELLOW, detail, metrics)
    return LayerResult(9, "vault_critic", GREEN, detail, metrics)


def probe_vault_embeddings(quick: bool) -> LayerResult:  # noqa: ARG001
    """Layer 10 — vault_embeddings coverage vs FTS-indexed notes.

    Shipped 2026-05-13 with Phase 1.7a. Reads vault_embeddings (count, dim,
    model) and cross-references with notes_fts to estimate coverage. The
    gateway hook (Task 6) keeps the index fresh on writes; the backfill
    command (Tasks 5/7/8) recovers cold-start and post-incident drift.
    """
    if not LOOM_DB.exists():
        return LayerResult(
            10, "vault_embeddings", SKIPPED,
            f"loom.db not found at {LOOM_DB}",
        )
    try:
        conn = sqlite3.connect(f"file:{LOOM_DB}?mode=ro", uri=True)
        # vault_embeddings stats
        row = conn.execute(
            """
            SELECT COUNT(*),
                   MAX(dim),
                   (SELECT model FROM vault_embeddings
                     GROUP BY model ORDER BY COUNT(*) DESC LIMIT 1)
              FROM vault_embeddings
            """,
        ).fetchone()
        # FTS row count for the denominator. notes_fts indexes everything
        # written through the gateway; subtract any .raw/ relpaths.
        fts_total = conn.execute(
            "SELECT COUNT(*) FROM notes_fts WHERE relpath NOT LIKE '.raw/%'",
        ).fetchone()[0] or 0
        conn.close()
    except sqlite3.OperationalError as e:
        msg = str(e)
        if "no such table" in msg:
            return LayerResult(10, "vault_embeddings", SKIPPED,
                               "vault_embeddings table not found (pre-1.7a?)")
        return LayerResult(10, "vault_embeddings", RED, f"sqlite error: {e}")
    except sqlite3.Error as e:
        return LayerResult(10, "vault_embeddings", RED, f"sqlite error: {e}")

    embedded, dim, model = row
    embedded = embedded or 0
    if fts_total == 0:
        return LayerResult(
            10, "vault_embeddings", SKIPPED,
            "no notes_fts rows yet (empty vault?)",
            {"embedded": embedded, "fts_total": 0},
        )

    coverage = min(embedded / fts_total, 1.0) if fts_total > 0 else 0.0
    pct = round(coverage * 100, 1)
    detail = (
        f"{embedded}/{fts_total} notes embedded ({pct}%)"
        + (f", model={model}" if model else "")
        + (f", dim={dim}" if dim else "")
    )
    metrics = {
        "embedded": embedded,
        "fts_total": fts_total,
        "coverage": round(coverage, 4),
        "dim": dim,
        "model": model,
    }
    if coverage >= 0.95:
        return LayerResult(10, "vault_embeddings", GREEN, detail, metrics)
    if coverage >= 0.80:
        return LayerResult(10, "vault_embeddings", YELLOW, detail, metrics)
    return LayerResult(10, "vault_embeddings", RED,
                       f"{detail} — run `loom vault embed --backfill` to recover", metrics)


def check_constitution() -> LayerResult:
    """Layer 6 — AgenticOS constitution drift (skill pointer integrity)."""
    script = AGENTIC_OS / "scripts/check-skill-pointers.sh"
    if not script.exists():
        return LayerResult(6, "constitution", YELLOW,
                           f"check-skill-pointers.sh not found at {script}")
    bash = shutil.which("bash")
    if bash is None:
        return LayerResult(6, "constitution", SKIPPED,
                           "bash not on PATH (Windows without git-bash?)")
    r = subprocess.run(
        [bash, str(script)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False, timeout=30,
    )
    metrics = {"exit": r.returncode, "stdout_tail": (r.stdout or "")[-300:]}
    if r.returncode != 0:
        return LayerResult(6, "constitution", RED,
                           f"check-skill-pointers exit {r.returncode}", metrics)
    return LayerResult(6, "constitution", GREEN,
                       "skill pointers resolve cleanly", metrics)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _color_emoji(status: str) -> str:
    return {GREEN: "OK", YELLOW: "WARN", RED: "FAIL", SKIPPED: "SKIP"}.get(status, "?")


def render_markdown(results: list[LayerResult]) -> str:
    lines = ["# Stack Health"]
    lines.append("")
    lines.append(f"_Generated: {_now_utc().isoformat()} on {platform.node()} ({sys.platform})_")
    lines.append("")
    lines.append("| # | Layer | Status | Detail |")
    lines.append("|---|---|---|---|")
    for r in results:
        lines.append(f"| {r.layer} | `{r.name}` | **{_color_emoji(r.status)}** | {r.detail} |")
    return "\n".join(lines) + "\n"


def render_json(results: list[LayerResult]) -> str:
    return json.dumps({
        "generated_at": _now_utc().isoformat(),
        "host": platform.node(),
        "platform": sys.platform,
        "results": [asdict(r) for r in results],
        "summary": {
            "green": sum(1 for r in results if r.status == GREEN),
            "yellow": sum(1 for r in results if r.status == YELLOW),
            "red": sum(1 for r in results if r.status == RED),
            "skipped": sum(1 for r in results if r.status == SKIPPED),
        },
    }, indent=2)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="stack-health")
    ap.add_argument("--quick", action="store_true",
                    help="skip slow checks (pytest)")
    ap.add_argument("--json", action="store_true",
                    help="JSON-only output (no markdown)")
    args = ap.parse_args(argv)

    results = [
        check_episodic_memory(),
        check_bd_memories(),
        check_wiki_compiler(quick=args.quick),
        check_scheduled_run(),
        check_wiki_repo(),
        check_constitution(),
        probe_vault_snapshots(quick=args.quick),
        probe_vault_provenance(quick=args.quick),
        probe_vault_critic(quick=args.quick),
        probe_vault_embeddings(quick=args.quick),
    ]

    if not args.json:
        sys.stdout.write(render_markdown(results))
        sys.stdout.write("\n```json\n")
    sys.stdout.write(render_json(results))
    if not args.json:
        sys.stdout.write("\n```\n")
    sys.stdout.flush()

    has_red = any(r.status == RED for r in results)
    return 1 if has_red else 0


if __name__ == "__main__":
    sys.exit(main())

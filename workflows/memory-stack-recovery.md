---
description: Recovery runbook for the 6-layer memory stack. One section per layer with exact diagnostic + repair commands. Source for VIOLATIONS.md cross-links.
---

# /memory-stack-recovery - Memory Stack Recovery

When `scripts/stack-health.py` reports any layer red or yellow, this is the runbook. Each layer has the same shape: **symptom**, **diagnostic command** (run it yourself, look at raw output), **likely cause**, **fix**. If the runbook doesn't match, capture the new failure mode here as you learn it.

## Why this exists

The 2026-05-06 session uncovered 8 cascading bugs in the Windows wiki-compiler stack that took ~10 days to surface. The diagnostic sequence to reach each one was non-obvious. This runbook captures those sequences so a future session reaches the fix in minutes instead of hours.

## When To Use

- `scripts/stack-health.py` shows red or yellow on any layer.
- A scheduled wiki-compile run has been failing for 2+ days (auto-bd-issue per Phase 1.3 should fire).
- The wiki repo's last commit is stale or has uncommitted state.
- Someone reports "I don't see my recent work in the wiki."

## Layer 1 — Episodic memory plugin DB

**Healthy:** `~/.config/superpowers/conversation-index/db.sqlite` has a `max(exchanges.timestamp)` within the last 24 hours.

**Diagnostic:**

```bash
python -c "
import sqlite3, pathlib
db = sqlite3.connect(str(pathlib.Path.home() / '.config/superpowers/conversation-index/db.sqlite'))
print(db.execute('SELECT MAX(timestamp), COUNT(*) FROM exchanges').fetchone())
"
```

**Likely causes:**

- Plugin disconnected, hook stopped firing.
- Indexing crashed silently; needs Claude Code restart.

**Fix:**

The 2026-04-27 → 2026-05-03 freeze on this machine **self-resolved** without code changes — Claude Code activity eventually rebuilt the indexer state. If a freeze is observed, first try a Claude Code session restart before assuming a deeper bug. If still stuck after a restart, the plugin install lives at `~/.claude/plugins/cache/superpowers-marketplace/episodic-memory` — last-resort: `claude plugin uninstall episodic-memory && claude plugin install superpowers-marketplace:episodic-memory`.

## Layer 2 — bd memories store + dolt remote

**Healthy:** `bd memories` returns a non-empty list AND `bd dolt remote list` includes `origin` AND last `bd dolt push` was within 7 days.

**Diagnostic:**

```bash
bd memories | head -3
bd dolt remote list
bd dolt log | head -3
```

**Likely causes:**

- Dolt remote unconfigured (new machine).
- Last `bd dolt push` skipped at session close.
- bd binary on PATH built without CGO and can't open embedded Dolt.

**Fix:**

- New machine: `bd dolt remote add origin git+ssh://git@github.com/lostforwurdz/beads-sync.git && bd dolt pull origin`
- Stale: `bd dolt push`
- CGO error ("embedded Dolt requires a CGO build"): identify which `bd.exe` Python's subprocess hits via `python -c "import shutil; print(shutil.which('bd'))"` versus the path that actually runs. If two `bd.exe` are on PATH, remove the broken one. See Layer 3 / sub-bug "subprocess shadowing" below.

## Layer 3 — wiki-compiler subprocess pipeline

This layer accumulated 8 sub-bugs in one session. Each has its own signature. Diagnose by symptom.

### 3a. Stale `bd.exe` shadows the working one (Windows)

**Symptom:** `bd memories` works in a shell but `subprocess.run(["bd", ...])` from Python fails with `embedded Dolt requires a CGO build` or returns wrong content.

**Diagnostic:**

```bash
python -c "import shutil; print(shutil.which('bd'))"
python -c "import subprocess; r=subprocess.run(['bd','--version'], capture_output=True, text=True); print(r.stdout.strip())"
```

If these disagree (e.g. `shutil.which` returns the npm `.CMD` shim but subprocess returns "1.0.3 (dev)" from a Go build), you have shadowing. Python's `CreateProcess` only matches `.exe` extensions; it skips `.CMD` shims when an unrelated `.exe` exists earlier on PATH.

**Fix (one-time):**

```bash
rm ~/go/bin/bd.exe          # whichever stale .exe shadows
# Drop ~/go/bin from user PATH via [Environment]::SetEnvironmentVariable
```

**Fix (defensive in code):**

`bd_source.py` and `llm.py` already use `shutil.which`-aware resolution per `_resolve_native_exe`. If a new tool spawns `bd` or `claude`, it must use the same pattern. See `wiki_compiler/llm.py:_resolve_native_exe` for reference.

### 3b. Multi-line `--system-prompt` truncated (Windows)

**Symptom:** `claude --print failed (exit 1): Warning: no stdin data received in 3s ... Input must be provided`. Compile reaches LLM stage but every call errors.

**Cause:** the `.CMD` shim wraps `claude.exe` via `cmd.exe %*`, and `cmd.exe` re-tokenizes args. Newlines in `--system-prompt` value terminate the line.

**Fix (in code):** write system prompt to a temp file, pass `--system-prompt-file <path>` instead. User prompt as positional arg directly to `claude.exe` (bypass `.CMD` via `_resolve_native_exe`). See `wiki-compiler@9939fbb`.

### 3c. UTF-8 decode bomb (Windows)

**Symptom:** `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position N: character maps to <undefined>`, then `TypeError: the JSON object must be str, bytes or bytearray, not NoneType`.

**Cause:** Python's `subprocess.run(text=True)` on Windows defaults to `locale.getpreferredencoding()` = `cp1252`. claude/bd emit UTF-8 (em-dashes, smart quotes, arrows). The decode thread crashes; `proc.stdout` becomes `None`; `json.loads(None)` raises.

**Fix:** pass `encoding="utf-8", errors="replace"` to `subprocess.run`. See `wiki-compiler@3e4e4d4`.

### 3d. `subprocess.TimeoutExpired` on real Claude calls

**Symptom:** Some `claude --print` calls take 3+ minutes; default 180s timeout fires.

**Fix:** bump `timeout=300` and wrap each item's processing in try/except so transient timeouts skip the item instead of killing the whole compile loop. See `wiki-compiler@3293e6c`.

### 3e. stderr-pipe deadlock during long runs

**Symptom:** Python at 0 CPU for hours during a wide-window compile. No new pages, no log entries.

**Cause:** wrapper script captures stderr via `*>> $LogFile` redirect with a fixed-size pipe buffer. If Python's per-item error logger writes hundreds of error lines (one per timeout), the buffer fills and Python's next `print(file=sys.stderr)` blocks indefinitely.

**Fix:** silent counter instead of per-item stderr writes; surface count via `RunStats.item_errors`. See `wiki-compiler@bacaaa6`.

### 3f. `import fcntl` fails on Windows

**Symptom:** `ModuleNotFoundError: No module named 'fcntl'` when `wiki-compile` starts.

**Fix:** branch `lock.py` on `sys.platform == "win32"` and use `msvcrt.locking(LK_NBLCK, 1)` instead. See `wiki-compiler@9e8cd5a`.

### 3g. `wiki-compile` not on Windows PATH

**Symptom:** wrapper logs `ERROR: wiki-compile not on PATH` daily; no compile runs.

**Cause:** `wiki-compile.exe` only lives in the venv `Scripts` dir which isn't on `$env:PATH`.

**Fix:** wrapper falls back to `$env:USERPROFILE\dev\wiki-compiler\.venv\Scripts\wiki-compile.exe` when `Get-Command` fails. See `wiki-compiler@00bc2dd`.

### 3h. Stuck process holding the lock

**Symptom:** New `wiki-compile` invocation exits 3 immediately with `another wiki-compile run holds`. But `Get-ChildItem` shows no current process.

**Diagnostic (Windows):**

```powershell
Get-Process | Where-Object { $_.Name -match 'wiki-compile|python|powershell' -and $_.CPU -lt 1 } | Format-Table Id, Name, StartTime, CPU
Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } | Select-Object ProcessId, ParentProcessId, CommandLine | Format-List
```

If the process is genuinely zombie:

```powershell
Stop-Process -Id <pid> -Force
```

The OS releases `msvcrt.locking` locks on process exit.

## Layer 4 — Scheduled wiki-compile run

**Healthy:** `~/.local/state/wiki-compiler/run.log` (Linux) or `%LOCALAPPDATA%\wiki-compiler\run.log` (Windows) has its most recent timestamp line within the last 30 hours, AND that run did not log `compile failed with exit 1`.

**Diagnostic:**

```bash
# Linux
systemctl --user list-timers wiki-compile.timer
systemctl --user status wiki-compile.service
tail ~/.local/state/wiki-compiler/run.log
```

```powershell
# Windows
Get-ScheduledTask -TaskName "wiki-compile" | Get-ScheduledTaskInfo
Get-Content "$env:LOCALAPPDATA\wiki-compiler\run.log" -Tail 30
```

**Likely causes:**

- Timer disabled.
- Wrapper exited with `wiki-compile not on PATH` (see Layer 3g).
- Run.log is mostly UTF-16 LE (Python tracebacks redirected through PowerShell). Decode raw bytes manually:

```powershell
$bytes = [System.IO.File]::ReadAllBytes("$env:LOCALAPPDATA\wiki-compiler\run.log")
[System.Text.Encoding]::Unicode.GetString($bytes) | Select-Object -Last 50
```

**Fix:** depends on cause. If the wrapper itself is broken, see the appropriate Layer 3 sub-bug. If the timer is disabled, re-enable.

### 4a. `indexer.py` crashes on non-UTF-8 wiki page (cascade-hider)

**Symptom:** Run log ends with `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xNN in position N: invalid start byte` from `wiki_compiler/indexer.py:_title_of`. Exit 1. No commit, no push. Layer 5 then shows uncommitted state because the wrapper's commit step never ran.

**Cause:** `_title_of(path)` used `path.read_text()` (UTF-8 strict by default). Pre-`3be1e72` wiki-compiler runs wrote `Reconciler` output with the platform encoding on Windows, leaving cp1252 bytes (`0x85` ellipsis, `0x97` em-dash, etc.) embedded in some pages. When a later run hits a per-item exception (e.g. `BudgetExceeded`), the `finally:` block in `compile.py` calls `rebuild_index`, which crashes on the first corrupt page. The UnicodeDecodeError **supplants** the original exception (since it's raised from inside `finally`), so the original error is masked AND the in-flight writes are stranded.

**Diagnostic:**

```bash
cd ~/wiki && python3 -c "
from pathlib import Path
for p in Path('.').rglob('*.md'):
    try: p.read_text()
    except UnicodeDecodeError as e: print(p, e)
"
```

**Fix:**

1. **In wiki-compiler** (one-time code fix): `_title_of` reads with `encoding="utf-8", errors="replace"` and wraps in `try/except OSError`; `compile.py` `finally:` block wraps `rebuild_index` + `append_run` in `try/except Exception` with single-line stderr (don't loop per-item — see 3e re: pipe deadlock). Shipped 2026-05-13.
2. **In the wiki repo** (one-time cleanup): re-encode each corrupt file from cp1252 to UTF-8 in place:

   ```bash
   cd ~/wiki && python3 -c "
   from pathlib import Path
   for fn in ['<rel/path/a.md>', '<rel/path/b.md>']:
       p = Path(fn); p.write_text(p.read_bytes().decode('cp1252'), encoding='utf-8')
   "
   ```

3. Sweep-commit per Layer 5 to recover the stranded writes from the masked run.

## Layer 5 — Compiled wiki repo state

**Healthy:** `~/wiki/.git` exists, `git status -sb` shows `## main...origin/main` (no ahead/behind, no dirty), last commit within 30 hours.

**Diagnostic:**

```bash
git -C ~/wiki status -sb
git -C ~/wiki log -1 --format='%h %ai %s'
```

**Likely causes:**

- Previous compile crashed mid-write, left uncommitted pages.
- Push failed due to network or auth issue.
- Local ahead of remote (push step skipped).

**Fix:**

```bash
git -C ~/wiki add -A
git -C ~/wiki commit -m "manual: sweep partial state"
git -C ~/wiki pull --rebase
git -C ~/wiki push
```

If the local has bad merges or regressions, revert to a known-good commit:

```bash
git -C ~/wiki log --oneline
git -C ~/wiki revert <bad-commit-sha>
git -C ~/wiki push
```

## Layer 6 — Constitution drift

**Healthy:** `bash ~/agenticOS/scripts/check-skill-pointers.sh` exits 0.

**Diagnostic:**

```bash
bash ~/agenticOS/scripts/check-skill-pointers.sh
```

**Likely cause:** A pointer skill in `~/agenticOS/skills/` references a plugin not currently installed.

**Fix:** install the plugin OR remove the pointer.

## When the runbook doesn't match

If you hit a failure mode not listed here, **add it before fixing it**. The cost of capturing a new symptom while the diagnostic is fresh is ~10 minutes; the cost of rediscovering it next time is hours. Add an entry under the right layer with: symptom, diagnostic command, cause, fix, link to the commit that addressed it.

## References

- `scripts/stack-health.py` — the probe that should fire this runbook.
- `bd memories | grep wiki-compiler` — durable memory keys per fix this session.
- `wiki-compiler` repo commit log — full diff of each sub-bug fix.
- `VIOLATIONS.md` — behavioral rules (cross-link from there to here).
- `CLAUDE.md` "Active Integrations" table — where this runbook is referenced from the constitution.

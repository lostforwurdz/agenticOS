#!/usr/bin/env bash
# install-linux.sh — symlink ~/.claude/* and ~/.gemini/skills into ~/agenticOS/
# Idempotent: safe to re-run. Replaces existing symlinks. Backs up real files.
set -euo pipefail

REPO="${REPO:-$HOME/agenticOS}"
CLAUDE="$HOME/.claude"
GEMINI="$HOME/.gemini"
BACKUP="$CLAUDE/_pre-symlink-backup-$(date +%Y%m%d-%H%M%S)"

if [[ ! -d "$REPO" ]]; then
  echo "ERROR: $REPO not found. Clone it first:"
  echo "  git clone https://github.com/lostforwurdz/agenticOS.git $REPO"
  exit 1
fi

mkdir -p "$CLAUDE" "$GEMINI"

# safe_link <target> <linkpath>
# - If linkpath is already the right symlink, skip
# - If linkpath is a different symlink, replace
# - If linkpath is a real file/dir with content, move to $BACKUP, then link
# - If linkpath does not exist, create
safe_link() {
  local target="$1" link="$2"
  if [[ -L "$link" ]]; then
    if [[ "$(readlink "$link")" == "$target" ]]; then
      echo "  ok    $link -> $target"
      return
    fi
    rm "$link"
  elif [[ -e "$link" ]]; then
    mkdir -p "$BACKUP"
    mv "$link" "$BACKUP/$(basename "$link")"
    echo "  backup $link -> $BACKUP/$(basename "$link")"
  fi
  ln -s "$target" "$link"
  echo "  link  $link -> $target"
}

echo "=== AgenticOS install (Linux) ==="
echo "Repo:    $REPO"
echo "Claude:  $CLAUDE"
echo "Gemini:  $GEMINI"
echo

safe_link "$REPO/CLAUDE.md"     "$CLAUDE/CLAUDE.md"
safe_link "$REPO/AGENTS.md"     "$CLAUDE/AGENTS.md"
safe_link "$REPO/VIOLATIONS.md" "$CLAUDE/VIOLATIONS.md"
safe_link "$REPO/agents"        "$CLAUDE/agents"
safe_link "$REPO/skills"        "$CLAUDE/skills"
safe_link "$REPO/workflows"     "$CLAUDE/workflows"
safe_link "$REPO/gemini/skills" "$GEMINI/skills"

echo
if [[ -d "$BACKUP" ]]; then
  echo "Backups saved to: $BACKUP"
fi

echo
echo "Verifying with claude mcp list..."
if command -v claude >/dev/null 2>&1; then
  claude mcp list || echo "  (claude not yet logged in or no MCPs configured)"
else
  echo "  claude CLI not in PATH; install Claude Code first"
fi

echo
echo "Done. Edit ~/.claude/CLAUDE.md and changes land in $REPO."

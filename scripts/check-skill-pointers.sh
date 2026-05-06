#!/usr/bin/env bash
# check-skill-pointers.sh — smoke check for thin pointer skills.
#
# PURPOSE:
#   Scans ~/agenticOS/skills/*.md (root-level only, no subdirs) for any
#   namespaced skill references (e.g. `engineering:code-review`). For each
#   reference found, verifies the named plugin is actually installed. Surfaces
#   ghost references before they silently fail at runtime.
#
# USAGE:
#   bash ~/agenticOS/scripts/check-skill-pointers.sh
#
# EXIT CODES:
#   0 — all pointer references resolve to installed plugins
#   1 — one or more BROKEN pointers (plugin not installed)
#   2 — prerequisite error (missing/malformed installed_plugins.json, no JSON parser)
#
# DEPENDENCIES: bash, grep, node (or jq if available)
# READ-ONLY: this script never modifies any file.

set -uo pipefail

SKILLS_DIR="${HOME}/agenticOS/skills"
PLUGINS_JSON="${HOME}/.claude/plugins/installed_plugins.json"
APPDATA_DIR="${APPDATA:-}"

# ---------------------------------------------------------------------------
# JSON parser selection: prefer jq, fall back to node
# ---------------------------------------------------------------------------
JSON_TOOL=""
if command -v jq >/dev/null 2>&1; then
  JSON_TOOL="jq"
elif command -v node >/dev/null 2>&1; then
  JSON_TOOL="node"
else
  echo "ERROR: no JSON parser available (need jq or node in PATH)" >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Verify installed_plugins.json exists and is readable
# ---------------------------------------------------------------------------
if [[ ! -f "$PLUGINS_JSON" ]]; then
  echo "ERROR: installed_plugins.json not found at: $PLUGINS_JSON" >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Extract installed plugin names from both known sources:
#   1. ~/.claude/plugins/installed_plugins.json  (marketplace installs)
#   2. $APPDATA/Claude/local-agent-mode-sessions/<account>/*/rpm/manifest.json
#      (RPM / cowork plugin installs, e.g. the `engineering` plugin)
# ---------------------------------------------------------------------------
get_installed_plugins_jq() {
  local plugins
  # Source 1: installed_plugins.json — keys are "name@marketplace", extract name
  plugins=$(jq -r '.plugins | keys[] | split("@")[0]' "$PLUGINS_JSON" 2>/dev/null)
  if [[ $? -ne 0 ]]; then
    echo "ERROR: installed_plugins.json is malformed (jq parse failed)" >&2
    exit 2
  fi

  # Source 2: RPM manifest (cowork plugin manager)
  if [[ -n "$APPDATA_DIR" ]]; then
    local cowork_file="${APPDATA_DIR}/Claude/cowork-enabled-cli-ops.json"
    if [[ -f "$cowork_file" ]]; then
      local account_id
      account_id=$(jq -r '.ownerAccountId // empty' "$cowork_file" 2>/dev/null)
      if [[ -n "$account_id" ]]; then
        local base_dir="${APPDATA_DIR}/Claude/local-agent-mode-sessions/${account_id}"
        if [[ -d "$base_dir" ]]; then
          while IFS= read -r -d '' mf; do
            jq -r '.plugins[]?.name // empty' "$mf" 2>/dev/null
          done < <(find "$base_dir" -maxdepth 3 -name "manifest.json" -path "*/rpm/*" -print0 2>/dev/null)
        fi
      fi
    fi
  fi

  echo "$plugins"
}

get_installed_plugins_node() {
  node -e "
const fs = require('fs');
const path = require('path');
const home = process.env.USERPROFILE || process.env.HOME;
const appdata = process.env.APPDATA || '';

// Source 1: installed_plugins.json
let names = [];
try {
  const ip = JSON.parse(fs.readFileSync(path.join(home, '.claude', 'plugins', 'installed_plugins.json'), 'utf8'));
  if (!ip || typeof ip.plugins !== 'object') {
    process.stderr.write('ERROR: installed_plugins.json is malformed\n');
    process.exit(2);
  }
  names = Object.keys(ip.plugins).map(k => k.split('@')[0]);
} catch(e) {
  process.stderr.write('ERROR: cannot read installed_plugins.json: ' + e.message + '\n');
  process.exit(2);
}

// Source 2: RPM manifest
if (appdata) {
  try {
    const coworkFile = path.join(appdata, 'Claude', 'cowork-enabled-cli-ops.json');
    if (fs.existsSync(coworkFile)) {
      const cw = JSON.parse(fs.readFileSync(coworkFile, 'utf8'));
      const accountId = cw.ownerAccountId;
      if (accountId) {
        const baseDir = path.join(appdata, 'Claude', 'local-agent-mode-sessions', accountId);
        if (fs.existsSync(baseDir)) {
          for (const sess of fs.readdirSync(baseDir)) {
            const mp = path.join(baseDir, sess, 'rpm', 'manifest.json');
            if (fs.existsSync(mp)) {
              const m = JSON.parse(fs.readFileSync(mp, 'utf8'));
              if (Array.isArray(m.plugins)) {
                names.push(...m.plugins.map(p => p.name).filter(Boolean));
              }
            }
          }
        }
      }
    }
  } catch(_) {}
}

// Deduplicate and print one per line
[...new Set(names)].forEach(n => console.log(n));
" 2>&1
  local exit_code=$?
  if [[ $exit_code -ne 0 ]]; then
    exit 2
  fi
}

# Collect installed plugin names into an array
declare -A INSTALLED_PLUGINS
while IFS= read -r plugin_name; do
  [[ -n "$plugin_name" ]] && INSTALLED_PLUGINS["$plugin_name"]=1
done < <(
  if [[ "$JSON_TOOL" == "jq" ]]; then
    get_installed_plugins_jq
  else
    get_installed_plugins_node
  fi
)

if [[ ${#INSTALLED_PLUGINS[@]} -eq 0 ]]; then
  echo "ERROR: could not extract any plugin names from installed_plugins.json" >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Scan root-level skill files for namespaced references (e.g. engineering:foo)
# ---------------------------------------------------------------------------
BROKEN=0
OK=0
FOUND_ANY=0

for skill_file in "${SKILLS_DIR}"/*.md; do
  [[ -f "$skill_file" ]] || continue
  skill_name=$(basename "$skill_file")

  # Find all namespace:skill patterns in the file body.
  # Pattern: word characters, colon, word characters (e.g. engineering:code-review)
  while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    FOUND_ANY=1
    plugin_ns="${ref%%:*}"   # part before first colon

    if [[ -n "${INSTALLED_PLUGINS[$plugin_ns]+_}" ]]; then
      echo "OK:     skills/${skill_name} -> ${ref} (plugin installed)"
      OK=$((OK + 1))
    else
      echo "BROKEN: skills/${skill_name} -> ${ref} (plugin NOT installed)"
      BROKEN=$((BROKEN + 1))
    fi
  done < <(
    grep -oE '[a-zA-Z][a-zA-Z0-9_-]+:[a-zA-Z][a-zA-Z0-9_-]+' "$skill_file" \
      | sort -u
  )
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo
echo "Installed plugins: $(IFS=', '; echo "${!INSTALLED_PLUGINS[*]}")"
echo "Pointers checked: $((OK + BROKEN))  |  OK: ${OK}  |  BROKEN: ${BROKEN}"

if [[ $FOUND_ANY -eq 0 ]]; then
  echo "No namespaced skill references found in ${SKILLS_DIR}/*.md"
  exit 0
fi

[[ $BROKEN -gt 0 ]] && exit 1
exit 0

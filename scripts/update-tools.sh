#!/bin/bash
# environment-awareness — TOOLS.md Writer
# Reads JSON scan results from stdin, writes TOOLS.md to the target workspace.
#
# Usage:
#   bash scan-environment.sh | bash update-tools.sh
#   bash scan-environment.sh --workspace ~/.openclaw/workspace-main | bash update-tools.sh

set -euo pipefail

FORCE=false
while [[ $# -gt 0 ]]; do
    case "$1" in --force) FORCE=true; shift ;; *) shift ;; esac
done

# Save stdin JSON to temp file
TMPFILE=$(mktemp -t envscan.XXXXXX.json)
trap "rm -f $TMPFILE" EXIT
cat > "$TMPFILE"

# Extract workspace
WORKSPACE=$(python3 -c "import json; d=json.load(open('$TMPFILE')); print(d.get('workspace',''))")
[[ -z "$WORKSPACE" ]] && { echo "ERROR: No workspace in scan data"; exit 1; }

TOOLS_MD="$WORKSPACE/TOOLS.md"

# Check for user-protected content in existing TOOLS.md
USER_CONTENT=""
if [[ -f "$TOOLS_MD" ]] && [[ "$FORCE" != true ]]; then
    USER_CONTENT=$(sed -n '/<!-- user:begin -->/,/<!-- user:end -->/p' "$TOOLS_MD" 2>/dev/null || echo "")
fi

# Generate TOOLS.md
python3 << PYEOF
import json, os

with open("$TMPFILE") as f:
    data = json.load(f)

ts = data.get("timestamp", "unknown")
ws = data.get("workspace", "")

L = []
def h(s=""): L.append(s)

h("# Tools & Environment")
h("")
h(f"> Auto-generated: {ts} | zhiming v1.0")
h("> To refresh: say \"scan environment\"")
h("")

# --- Search & Retrieval ---
h("## Search & Retrieval (Priority ↓)")
h("")
h("| Priority | Tool | CLI | Status | API Key | Notes |")
h("|----------|------|-----|--------|---------|-------|")

key_hints = {"Tavily Search": "TAVILY_API_KEY", "Agent-Reach": "", "Jina Reader": "JINA_API_KEY", "GitHub CLI": "GITHUB_TOKEN"}
api_found = {k["variable"] for k in data.get("api_keys", [])}

for idx, t in enumerate(data.get("search_tools", []), 1):
    name = t["name"]
    cli = t["cli"]
    ok = t.get("available", False)
    status = "✅" if ok else "❌"
    kh = key_hints.get(name, "")
    ks = f"\${kh}" if kh and kh in api_found else ("not set" if kh else "—")
    notes = t.get("version", "") if ok else ""
    h(f"| {idx} | {name} | \`{cli}\` | {status} | {ks} | {notes} |")

h(f"| {idx+1} | web_search | built-in | ✅ | — | Built-in lightweight search |")
h(f"| {idx+2} | web_fetch | built-in | ✅ | — | Built-in page fetcher |")
h("")

# --- Model Providers ---
h("## Model Providers")
h("")
h("| Provider | API Type | Representative Models |")
h("|----------|----------|----------------------|")
for p in data.get("model_providers", []):
    h(f"| {p['provider']} | {p['api_type']} | {p['representative_models']} |")
h("")

# --- Installed Skills ---
h("## Installed Skills")
h("")
h("| Skill | Status | Purpose |")
h("|-------|--------|---------|")
for s in data.get("skills", []):
    en = s.get("enabled", "unknown")
    icon = "✅ enabled" if en == "true" else ("❌ disabled" if en == "false" else "— unknown")
    desc = s.get("description", "")[:80]
    h(f"| {s['name']} | {icon} | {desc} |")
h("")

# --- CLI Toolkit ---
h("## CLI Toolkit")
h("")
h("| Tool | Version |")
h("|------|---------|")
for t in data.get("cli_tools", []):
    if t.get("available"):
        h(f"| \`{t['name']}\` | {t['version']} |")
h("")

# --- Communication Channels ---
h("## Communication Channels")
h("")
h("| Channel | Status |")
h("|---------|--------|")
for ch in data.get("channels", []):
    icon = "✅" if ch.get("enabled") else "❌"
    h(f"| {ch['name']} | {icon} |")
h("")

# --- Workspace Files ---
h("## Workspace Files")
h("")
h("| File | Status |")
h("|------|--------|")
for f in data.get("workspace_files", []):
    icon = "✅" if f.get("exists") else "❌"
    h(f"| {f['file']} | {icon} |")
h("")

# --- API Keys Summary ---
api_vars = [k["variable"] for k in data.get("api_keys", [])]
if api_vars:
    h("## API Keys Detected")
    h("")
    h("Environment variables found (names only, values never stored):")
    h("")
    for v in api_vars:
        h(f"- \`{v}\`")
    h("")

h("---")

output = "\n".join(L)

# Write file
os.makedirs(os.path.dirname("$TOOLS_MD"), exist_ok=True)
with open("$TOOLS_MD", "w") as f:
    f.write(output)

# Count stats
lines_written = len(L)
size = len(output)
print(f"TOOLS.md written: $TOOLS_MD ({lines_written} lines, {size} bytes)")
PYEOF

# Append user-protected sections if any
if [[ -n "$USER_CONTENT" ]]; then
    echo "" >> "$TOOLS_MD"
    echo "$USER_CONTENT" >> "$TOOLS_MD"
fi

echo "Done."

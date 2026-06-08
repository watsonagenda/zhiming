#!/bin/bash
# zhiming — System Environment Scanner
# Scans system environment and outputs JSON to stdout.
# Usage: bash scan-environment.sh [--workspace ~/.openclaw/workspace-main]
set -euo pipefail

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
while [[ $# -gt 0 ]]; do
    case "$1" in --workspace) WORKSPACE="$2"; shift 2 ;; *) shift ;; esac
done
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
export WORKSPACE TIMESTAMP

python3 << 'PYEOF'
import json, os, subprocess, sys
from datetime import datetime

ws = os.environ.get("WORKSPACE", os.path.expanduser("~/.openclaw/workspace"))
ts = os.environ.get("TIMESTAMP", datetime.utcnow().isoformat())
openclaw_json = os.path.expanduser("~/.openclaw/openclaw.json")

def which(cmd):
    """Check if command exists, return path or empty."""
    try:
        return subprocess.run(["command", "-v", cmd], capture_output=True, text=True).stdout.strip()
    except:
        return ""

def version(cmd, extract=None):
    """Get version of a CLI tool."""
    try:
        r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
        out = r.stdout.strip() or r.stderr.strip()
        if extract:
            import re
            m = re.search(extract, out)
            return m.group(1) if m else out.split("\n")[0][:60]
        return out.split("\n")[0][:60]
    except:
        return ""

# --- 1. Search & Retrieval Tools ---
search_tools = [
    {"name": "Tavily Search", "cli": "tvly"},
    {"name": "Agent-Reach", "cli": "mcporter"},
    {"name": "Jina Reader", "cli": "jina"},
    {"name": "GitHub CLI", "cli": "gh"},
]
for t in search_tools:
    p = which(t["cli"])
    t["path"] = p
    t["available"] = bool(p)
    t["version"] = version(t["cli"]).split("\n")[0][:80] if p else ""

# --- 2. API Key Environment Variables ---
api_keys = []
# Sensitive prefixes to skip
skip_prefixes = ("SECURITY_", "OAUTH_", "PRIVATE_", "CERT_", "KEYCHAIN_", "GATEWAY_")
for k, v in sorted(os.environ.items()):
    if any(k.lower().endswith(s) for s in ("_api_key", "_token", "_secret")):
        if not any(k.startswith(p) for p in skip_prefixes):
            api_keys.append({"variable": k})

# --- 3. Model Providers ---
model_providers = []
if os.path.exists(openclaw_json):
    try:
        with open(openclaw_json) as f:
            cfg = json.load(f)
        providers = cfg.get("models", {}).get("providers", {})
        for name, p in providers.items():
            models = p.get("models", [])
            rep = ", ".join([m.get("id", "?") for m in models[:3]])
            model_providers.append({
                "provider": name,
                "api_type": p.get("api", "unknown"),
                "representative_models": rep
            })
    except:
        pass

# --- 4. Installed Skills ---
skills = []
skill_status = {}
if os.path.exists(openclaw_json):
    try:
        with open(openclaw_json) as f:
            cfg = json.load(f)
        entries = cfg.get("skills", {}).get("entries", {})
        for name, e in entries.items():
            skill_status[name] = str(e.get("enabled", False)).lower()
    except:
        pass

for skills_dir in [
    os.path.expanduser("~/.openclaw/skills"),
    os.path.join(ws, "skills")
]:
    if not os.path.isdir(skills_dir):
        continue
    try:
        for entry in sorted(os.listdir(skills_dir)):
            skill_path = os.path.join(skills_dir, entry)
            if not os.path.isdir(skill_path):
                continue
            skill_md = os.path.join(skill_path, "SKILL.md")
            desc = ""
            if os.path.exists(skill_md):
                try:
                    with open(skill_md) as f:
                        lines = f.readlines()
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        if line.startswith("description:"):
                            val = line.split(":", 1)[1].strip()
                            # Handle block scalars: |, >, |-, >-, |+, >+
                            if val and val[0] in ('|', '>'):
                                # Collect indented continuation lines
                                desc_parts = []
                                i += 1
                                while i < len(lines) and (lines[i].startswith('  ') or lines[i].startswith('\t') or lines[i].strip() == ''):
                                    if lines[i].strip():
                                        desc_parts.append(lines[i].strip())
                                    i += 1
                                desc = ' '.join(desc_parts)[:200]
                            else:
                                desc = val.strip('"').strip("'")[:200]
                            break
                        i += 1
                except:
                    pass
            skills.append({
                "name": entry,
                "path": skill_path,
                "description": desc,
                "enabled": skill_status.get(entry, "unknown")
            })
    except:
        pass

# --- 5. Communication Channels ---
channels = []
if os.path.exists(openclaw_json):
    try:
        with open(openclaw_json) as f:
            cfg = json.load(f)
        for name, ch in cfg.get("channels", {}).items():
            channels.append({
                "name": name,
                "enabled": bool(ch.get("enabled", False))
            })
    except:
        pass

# --- 6. System CLI Tools ---
cli_tools = [
    {"name": "git", "extract": r"(\d+\.\d+\.\d+)"},
    {"name": "docker", "extract": r"(\d+\.\d+\.\d+)"},
    {"name": "python3", "extract": r"(\d+\.\d+\.\d+)"},
    {"name": "node", "extract": r"v(\d+\.\d+\.\d+)"},
    {"name": "ffmpeg", "extract": r"(\d+\.\d+)"},
    {"name": "magick", "extract": r"(\d+\.\d+\.\d+)"},
    {"name": "pandoc", "extract": r"(\d+\.\d+)"},
    {"name": "curl", "extract": r"(\d+\.\d+\.\d+)"},
    {"name": "wget", "extract": r"(\d+\.\d+\.\d+)"},
    {"name": "jq", "extract": r"(\d+\.\d+)"},
    {"name": "sqlite3", "extract": r"(\d+\.\d+\.\d+)"},
    {"name": "rg", "extract": r"(\d+\.\d+\.\d+)"},
    {"name": "fd", "extract": r"(\d+\.\d+\.\d+)"},
    {"name": "bat", "extract": r"(\d+\.\d+\.\d+)"},
]
for t in cli_tools:
    p = which(t["name"])
    t["path"] = p
    t["available"] = bool(p)
    t["version"] = version(t["name"], t.get("extract")) if p else ""

# --- 7. Workspace Files ---
ws_files_cfg = ["AGENTS.md", "SOUL.md", "MEMORY.md", "TOOLS.md", "USER.md", "DREAMS.md", "IDENTITY.md"]
ws_files = []
for f in ws_files_cfg:
    ws_files.append({
        "file": f,
        "exists": os.path.exists(os.path.join(ws, f))
    })

# --- Assemble & Output ---
result = {
    "timestamp": ts,
    "workspace": ws,
    "search_tools": search_tools,
    "api_keys": api_keys,
    "model_providers": model_providers,
    "skills": skills,
    "channels": channels,
    "cli_tools": cli_tools,
    "workspace_files": ws_files
}
print(json.dumps(result, indent=2, ensure_ascii=False))
PYEOF

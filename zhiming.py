#!/usr/bin/env python3
"""
ZhiMing (知明) — AI Agent Self-Awareness Toolkit

Single-script environment scanner and TOOLS.md renderer.
Replaces scan-environment.sh + update-tools.sh + run.sh + demo.py.

Usage:
    python3 zhiming.py --json          # Output JSON to stdout (pipe-friendly)
    python3 zhiming.py --demo          # Human-readable summary
    python3 zhiming.py                 # Default: scan + write TOOLS.md
    python3 zhiming.py --force         # Full rebuild, discard user content
    python3 zhiming.py --workspace /path/to/ws  # Target specific workspace

Import-friendly:
    from zhiming import scan_all
    result = scan_all(workspace="/path/to/ws")
"""

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

OPENCLAW_JSON = os.path.expanduser("~/.openclaw/openclaw.json")
SKILLS_DIR_FRAMEWORK = os.path.expanduser("~/.openclaw/skills")
DEFAULT_WORKSPACE = os.environ.get(
    "OPENCLAW_WORKSPACE", os.path.expanduser("~/.openclaw/workspace")
)

SKIP_KEY_PREFIXES = (
    "SECURITY_", "OAUTH_", "PRIVATE_", "CERT_", "KEYCHAIN_", "GATEWAY_",
)

WS_FILES = [
    "AGENTS.md", "SOUL.md", "MEMORY.md", "TOOLS.md",
    "USER.md", "DREAMS.md", "IDENTITY.md",
]

KEY_HINTS = {
    "Tavily Search": "TAVILY_API_KEY",
    "Agent-Reach": "",
    "Jina Reader": "JINA_API_KEY",
    "GitHub CLI": "GITHUB_TOKEN",
}

SEARCH_TOOLS_DEF = [
    {"name": "Tavily Search", "cli": "tvly"},
    {"name": "Agent-Reach", "cli": "mcporter"},
    {"name": "Jina Reader", "cli": "jina"},
    {"name": "GitHub CLI", "cli": "gh"},
]

CLI_TOOLS_DEF = [
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

CACHE_TTL = 300  # 5 minutes


# ─────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────

def _which(cmd: str) -> str:
    """Return path to command, or empty string if not found."""
    try:
        return subprocess.run(
            ["command", "-v", cmd], capture_output=True, text=True, timeout=3
        ).stdout.strip()
    except Exception:
        return ""


def _version(cmd: str, extract: str | None = None) -> str:
    """Get version string for a CLI tool, with optional regex extraction."""
    try:
        r = subprocess.run(
            [cmd, "--version"], capture_output=True, text=True, timeout=5
        )
        out = (r.stdout.strip() or r.stderr.strip()).split("\n")[0][:80]
        if extract:
            m = re.search(extract, out)
            if m:
                return m.group(1)
        return out
    except Exception:
        return ""


def _parse_skill_md(filepath: str) -> str:
    """Extract description from YAML frontmatter of a SKILL.md.

    Handles block scalars (|, >, |-, >-, |+, >+).
    """
    try:
        with open(filepath) as f:
            lines = f.readlines()
    except Exception:
        return ""

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("description:"):
            val = line.split(":", 1)[1].strip()
            if val and val[0] in ("|", ">"):
                # Block scalar — collect indented continuation lines
                desc_parts = []
                i += 1
                while i < len(lines) and (
                    lines[i].startswith("  ")
                    or lines[i].startswith("\t")
                    or lines[i].strip() == ""
                ):
                    if lines[i].strip():
                        desc_parts.append(lines[i].strip())
                    i += 1
                return " ".join(desc_parts)[:200]
            else:
                return val.strip("\"' ")[:200]
        i += 1
    return ""


def _load_json(path: str):
    """Load and parse a JSON file, returning {} on any failure."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _load_user_content(tools_md: str) -> str:
    """Extract user content between <!-- user:begin --> and <!-- user:end -->."""
    if not os.path.exists(tools_md):
        return ""
    try:
        with open(tools_md) as f:
            text = f.read()
        m = re.search(
            r"<!--\s*user:begin\s*-->.*?<!--\s*user:end\s*-->",
            text, re.DOTALL
        )
        if m:
            return m.group(0)
    except Exception:
        pass
    return ""


# ─────────────────────────────────────────────────────────────
# Scan dimensions (each is a standalone function)
# ─────────────────────────────────────────────────────────────

def scan_search_tools() -> list[dict]:
    """Dimension 1: Search & retrieval tools."""
    result = []
    for t in SEARCH_TOOLS_DEF:
        p = _which(t["cli"])
        result.append({
            "name": t["name"],
            "cli": t["cli"],
            "path": p,
            "available": bool(p),
            "version": _version(t["cli"]) if p else "",
        })
    return result


def scan_api_keys() -> list[dict]:
    """Dimension 2: API key env vars (names only, never values)."""
    result = []
    for k in sorted(os.environ):
        lower = k.lower()
        if any(lower.endswith(s) for s in ("_api_key", "_token", "_secret")):
            if not any(k.startswith(p) for p in SKIP_KEY_PREFIXES):
                result.append({"variable": k})
    return result


def scan_model_providers() -> list[dict]:
    """Dimension 3: Model providers from openclaw.json."""
    cfg = _load_json(OPENCLAW_JSON)
    providers = cfg.get("models", {}).get("providers", {})
    result = []
    for name, p in providers.items():
        models = p.get("models", [])
        rep = ", ".join([m.get("id", "?") for m in models[:3]])
        result.append({
            "provider": name,
            "api_type": p.get("api", "unknown"),
            "representative_models": rep,
        })
    return result


def scan_skills(workspace: str) -> list[dict]:
    """Dimension 4: Installed skills with enabled status."""
    cfg = _load_json(OPENCLAW_JSON)
    entries = cfg.get("skills", {}).get("entries", {})
    status_map = {n: str(e.get("enabled", False)).lower() for n, e in entries.items()}

    result = []
    for skills_dir in [SKILLS_DIR_FRAMEWORK, os.path.join(workspace, "skills")]:
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
                        desc = _parse_skill_md(skill_md)
                    except Exception:
                        pass
                result.append({
                    "name": entry,
                    "path": skill_path,
                    "description": desc,
                    "enabled": status_map.get(entry, "unknown"),
                })
        except Exception:
            pass
    return result


def scan_channels() -> list[dict]:
    """Dimension 5: Communication channels."""
    cfg = _load_json(OPENCLAW_JSON)
    result = []
    for name, ch in cfg.get("channels", {}).items():
        result.append({
            "name": name,
            "enabled": bool(ch.get("enabled", False)),
        })
    return result


def scan_cli_tools() -> list[dict]:
    """Dimension 6: System CLI tools with concurrent version checks."""

    def _check(tool_def):
        name = tool_def["name"]
        p = _which(name)
        if not p:
            return {
                "name": name,
                "path": "",
                "available": False,
                "version": "",
            }
        ver = _version(name, tool_def.get("extract"))
        return {
            "name": name,
            "path": p,
            "available": True,
            "version": ver,
        }

    # Phase 1: which() is fast, do sequentially
    # Phase 2: version checks are concurrent (each capped at timeout)
    with concurrent.futures.ThreadPoolExecutor(max_workers=14) as ex:
        futures = {ex.submit(_check, td): td for td in CLI_TOOLS_DEF}
        results = []
        for f in concurrent.futures.as_completed(futures, timeout=10):
            try:
                results.append(f.result(timeout=2))
            except Exception:
                td = futures[f]
                results.append({
                    "name": td["name"],
                    "path": "",
                    "available": False,
                    "version": "",
                })
    # Sort in original order
    order = {td["name"]: i for i, td in enumerate(CLI_TOOLS_DEF)}
    results.sort(key=lambda r: order.get(r["name"], 99))
    return results


def scan_workspace_files(workspace: str) -> list[dict]:
    """Dimension 7: Workspace file existence."""
    return [
        {"file": f, "exists": os.path.exists(os.path.join(workspace, f))}
        for f in WS_FILES
    ]


# ─────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────

def scan_all(workspace: str | None = None) -> dict:
    """Run all 7 scan dimensions and return a unified result dict.

    Can be imported: from zhiming import scan_all
    """
    ws = workspace or DEFAULT_WORKSPACE
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Execute all scans ---
    # These are ordered and can run sequentially — the CLI tools dimension
    # already does its own internal concurrency. Scan functions are I/O-bound
    # and lightweight; keeping iteration order is preferred over parallelism
    # here for predictable behavior.
    result = {
        "timestamp": ts,
        "workspace": ws,
        "search_tools": scan_search_tools(),
        "api_keys": scan_api_keys(),
        "model_providers": scan_model_providers(),
        "skills": scan_skills(ws),
        "channels": scan_channels(),
        "cli_tools": scan_cli_tools(),
        "workspace_files": scan_workspace_files(ws),
    }

    return result


# ─────────────────────────────────────────────────────────────
# Rendering engine (TOOLS.md)
# ─────────────────────────────────────────────────────────────

def render_tools_md(data: dict, force: bool, workspace: str) -> str:
    """Render TOOLS.md Markdown from scan results and write atomically."""
    ts = data.get("timestamp", "unknown")

    L = []

    def h(s=""):
        L.append(s)

    h("# Tools & Environment")
    h("")
    h(f"> Auto-generated: {ts} | zhiming v1.1")
    h('> To refresh: say "scan environment"')
    h("")

    # --- Search & Retrieval ---
    h("## Search & Retrieval (Priority ↓)")
    h("")
    h("| Priority | Tool | CLI | Status | API Key | Notes |")
    h("|----------|------|-----|--------|---------|-------|")

    api_found = {k["variable"] for k in data.get("api_keys", [])}
    idx = 0
    for t in data.get("search_tools", []):
        idx += 1
        name = t["name"]
        cli = t["cli"]
        ok = t.get("available", False)
        status = "✅" if ok else "❌"
        kh = KEY_HINTS.get(name, "")
        if kh:
            ks = f"${kh}" if kh in api_found else "not set"
        else:
            ks = "—"
        notes = t.get("version", "") if ok else ""
        h(f"| {idx} | {name} | `{cli}` | {status} | {ks} | {notes} |")

    h(f"| {idx + 1} | web_search | built-in | ✅ | — | Built-in lightweight search |")
    h(f"| {idx + 2} | web_fetch | built-in | ✅ | — | Built-in page fetcher |")
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
        stem = s.get("description", "")[:80]
        if en == "true":
            icon = "✅ enabled"
        elif en == "false":
            icon = "❌ disabled"
        else:
            icon = "— unknown"
        h(f"| {s['name']} | {icon} | {stem} |")
    h("")

    # --- CLI Toolkit ---
    h("## CLI Toolkit")
    h("")
    h("| Tool | Version |")
    h("|------|---------|")
    for t in data.get("cli_tools", []):
        if t.get("available"):
            h(f"| `{t['name']}` | {t['version']} |")
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
            h(f"- `{v}`")
        h("")

    h("---")
    h("")

    output = "\n".join(L)

    # --- Atomic write ---
    tools_md = os.path.join(workspace, "TOOLS.md")
    tmp = tools_md + ".tmp"

    os.makedirs(workspace, exist_ok=True)
    with open(tmp, "w") as f:
        f.write(output)

    # Preserve user content unless forced
    if not force:
        uc = _load_user_content(tools_md)
        if uc:
            with open(tmp, "a") as f:
                f.write("\n" + uc + "\n")

    os.rename(tmp, tools_md)
    return tools_md


# ─────────────────────────────────────────────────────────────
# Demo / summary mode
# ─────────────────────────────────────────────────────────────

def demo_summary(data: dict) -> str:
    """Return a human-readable summary string (like old demo.py)."""
    L = []
    L.append("=" * 66)
    L.append("  ZhiMing (知明) — Environment Scanner")
    L.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    L.append("=" * 66)
    L.append("")
    L.append(f"Workspace: {data.get('workspace', '?')}")
    L.append("")

    # Search tools
    L.append("Search Tools:")
    for t in data.get("search_tools", []):
        s = "Y" if t.get("available") else "N"
        L.append(f"  [{s}] {t['name']:28s} cli={t['cli']:12s}")
    L.append("")

    # Model providers
    L.append("Model Providers:")
    for p in data.get("model_providers", []):
        models_str = p.get("representative_models", "")
        models = [m.strip() for m in models_str.split(",") if m.strip()]
        top3 = models[:3]
        extra = f"  (+{len(models) - 3} more)" if len(models) > 3 else ""
        L.append(f"  {p['provider']:20s} ({p['api_type']}){extra}")
        for m in top3:
            L.append(f"    - {m}")
    L.append("")

    # Skills
    skills = data.get("skills", [])
    enabled = [s for s in skills if s.get("enabled") == "true"]
    disabled = [s for s in skills if s.get("enabled") == "false"]
    unknown = [s for s in skills if s.get("enabled") == "unknown"]
    L.append(
        f"Skills: {len(enabled)} enabled, {len(disabled)} disabled, "
        f"{len(unknown)} unknown"
    )
    for s in skills:
        en = s.get("enabled", "unknown")
        icon = "+" if en == "true" else ("-" if en == "false" else "?")
        desc = s.get("description", "")[:60]
        L.append(f"  [{icon}] {s['name']:32s} {desc}")
    L.append("")

    # CLI tools
    available_cli = [t for t in data.get("cli_tools", []) if t.get("available")]
    L.append(f"CLI Tools: {len(available_cli)} detected")
    for t in available_cli:
        L.append(f"  {t['name']:12s} {t['version']}")
    L.append("")

    # Channels
    L.append("Channels:")
    for ch in data.get("channels", []):
        icon = "+" if ch.get("enabled") else "-"
        L.append(f"  [{icon}] {ch['name']}")
    L.append("")

    # API keys
    apikeys = data.get("api_keys", [])
    L.append(f"API Keys in environment: {len(apikeys)}")
    for k in apikeys:
        L.append(f"  - {k.get('variable', k)}")
    L.append("")

    # Workspace files
    ws_files = data.get("workspace_files", [])
    existing = [f for f in ws_files if f.get("exists")]
    missing = [f for f in ws_files if not f.get("exists")]
    L.append(f"Workspace files: {len(existing)} present, {len(missing)} missing")
    for f in ws_files:
        icon = "+" if f.get("exists") else "-"
        L.append(f"  [{icon}] {f['file']}")
    L.append("")

    total_models = sum(
        len([m.strip() for m in p.get("representative_models", "").split(",") if m.strip()])
        for p in data.get("model_providers", [])
    )
    L.append(f"Total models: {total_models}")
    L.append("")
    L.append("=" * 66)

    return "\n".join(L)


# ─────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ZhiMing (知明) — AI Agent Self-Awareness Toolkit"
    )
    parser.add_argument(
        "--workspace", "-w",
        default=None,
        help="Target workspace path (default: $OPENCLAW_WORKSPACE or ~/.openclaw/workspace)",
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Output a human-readable summary (no file writes)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON to stdout (pipe-friendly)",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force full rebuild, discard user content in TOOLS.md",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip cache, force re-scan",
    )
    args = parser.parse_args()

    workspace = args.workspace or DEFAULT_WORKSPACE
    use_cache = not args.no_cache

    data = scan_all(workspace=workspace, use_cache=use_cache)

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.demo:
        print(demo_summary(data))
    else:
        written = render_tools_md(data, force=args.force, workspace=workspace)
        lines = len(data.__repr__())  # approximate — just report path
        print(f"TOOLS.md written: {written}")


if __name__ == "__main__":
    main()

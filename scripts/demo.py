#!/usr/bin/env python3
"""zhiming demo — display scan results in a human-friendly summary."""

import json, subprocess, sys
from datetime import datetime

SCAN_SCRIPT = sys.argv[1] if len(sys.argv) > 1 else "scripts/scan-environment.sh"

def main():
    result = subprocess.run(["bash", SCAN_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERR: scan failed — {result.stderr}")
        sys.exit(1)

    d = json.loads(result.stdout)

    print("=" * 66)
    print("  Environment Awareness Scanner — Demo")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 66)
    print()
    print(f"Workspace: {d.get('workspace', '?')}")
    print()

    # Search tools
    print("Search Tools:")
    for t in d.get('search_tools', []):
        s = 'Y' if t.get('available') else 'N'
        print(f"  [{s}] {t['name']:28s} cli={t['cli']:12s}")
    print()

    # Model providers
    print("Model Providers:")
    for p in d.get('model_providers', []):
        models_str = p.get('representative_models', '')
        models = [m.strip() for m in models_str.split(',') if m.strip()]
        top3 = models[:3]
        extra = f"  (+{len(models)-3} more)" if len(models) > 3 else ""
        print(f"  {p['provider']:20s} ({p['api_type']}){extra}")
        for m in top3:
            print(f"    - {m}")
    print()

    # Skills
    skills = d.get('skills', [])
    enabled = [s for s in skills if s.get('enabled') == 'true']
    disabled = [s for s in skills if s.get('enabled') == 'false']
    unknown = [s for s in skills if s.get('enabled') == 'unknown']
    print(f"Skills: {len(enabled)} enabled, {len(disabled)} disabled, {len(unknown)} unknown")
    for s in skills:
        icon = '+' if s.get('enabled') == 'true' else ('-' if s.get('enabled') == 'false' else '?')
        desc = s.get('description', '')[:60]
        print(f"  [{icon}] {s['name']:32s} {desc}")
    print()

    # CLI tools
    available_cli = [t for t in d.get('cli_tools', []) if t.get('available')]
    print(f"CLI Tools: {len(available_cli)} detected")
    for t in available_cli:
        print(f"  {t['name']:12s} {t['version']}")
    print()

    # Channels
    print("Channels:")
    for ch in d.get('channels', []):
        icon = '+' if ch.get('enabled') else '-'
        print(f"  [{icon}] {ch['name']}")
    print()

    # API keys
    apikeys = d.get('api_keys', [])
    print(f"API Keys in environment: {len(apikeys)}")
    for k in apikeys:
        print(f"  - {k.get('variable', k)}")
    print()

    # Workspace files
    ws_files = d.get('workspace_files', [])
    existing = [f for f in ws_files if f.get('exists')]
    missing = [f for f in ws_files if not f.get('exists')]
    print(f"Workspace files: {len(existing)} present, {len(missing)} missing")
    for f in ws_files:
        icon = '+' if f.get('exists') else '-'
        print(f"  [{icon}] {f['file']}")
    print()

    total_models = sum(
        len([m.strip() for m in p.get('representative_models', '').split(',') if m.strip()])
        for p in d.get('model_providers', [])
    )
    print(f"Total models: {total_models}")
    print()
    print("=" * 66)
    print("  Run 'bash run.sh' to write results to your workspace.")
    print("=" * 66)

if __name__ == "__main__":
    main()

---
name: zhiming
description: "Scans the local system environment and writes a structured inventory to TOOLS.md, so every new session knows exactly which tools, APIs, models, and skills are available."
---

# zhiming — AI Agent Self-Awareness Toolkit

Scans the local system environment and writes a structured inventory to `TOOLS.md`.
Framework-agnostic: auto-detects OpenClaw, Claude Code, Cline, Continue, and Cursor,
with manual overrides via `--config` / `--skills-dir` / `--workspace`.

## When to Run

| Trigger | Condition |
|---------|-----------|
| Manual | User says "scan environment", "update tools", "refresh environment", "扫描环境", "更新工具", "刷新环境", etc. |
| Gap detected | Agent tries to use a tool/API not in TOOLS.md and fails or gets confused |

**Do NOT run:** every session start, timed schedules, or normal task execution.

## Scan Dimensions (7 total)

1. **Search tools**: tvly, mcporter, jina, gh — detected via `command -v`
2. **API keys**: env vars matching `*_API_KEY`, `*_TOKEN`, `*_SECRET` (names only, never values)
3. **Model providers**: parsed from `{config_path}` → providers section, top 3 models each
4. **Installed skills**: scanned from `{skills_dir}` and `{workspace}/skills/`, description from SKILL.md frontmatter
5. **Communication channels**: from `{config_path}` → channels section (if supported by framework)
6. **CLI toolkit**: git, docker, python3, node, ffmpeg, magick, pandoc, curl, wget, jq, sqlite3, rg, fd, bat — concurrent version checks
7. **Workspace files**: framework-specific key files (e.g. AGENTS.md, CLAUDE.md, TOOLS.md, .cursorrules)

## Supported Frameworks

| Framework | Config Path | Skills Dir | Workspace | Auto-Detect |
|-----------|------------|-----------|-----------|:---:|
| OpenClaw | `~/.openclaw/openclaw.json` | `~/.openclaw/skills` | `~/.openclaw/workspace` | Yes |
| Claude Code | `~/.claude/claude_desktop_config.json` | `~/.claude/skills` | `~/.claude/workspace` | Yes |
| Cline | `~/.cline/config.json` | `~/.cline/skills` | `~/.cline/workspace` | Yes |
| Continue | `~/.continue/config.json` | `~/.continue/skills` | `~/.continue/workspace` | Yes |
| Cursor | `~/.cursor/mcp.json` | `~/.cursor/skills` | `~/.cursor/workspace` | Yes |

Frameworks are detected automatically by checking for their default config files.
Use `--framework` to override or `--config` / `--skills-dir` / `--workspace` for custom paths.

## Usage

```bash
# Auto-detect framework and scan
python3 zhiming.py

# Scan + update TOOLS.md
python3 zhiming.py --workspace /path/to/ws

# Human-readable summary
python3 zhiming.py --demo

# Raw JSON to stdout
python3 zhiming.py --json

# Full rebuild (discard user content)
python3 zhiming.py --force
```

For non-standard paths or unsupported frameworks:

```bash
python3 zhiming.py --config /path/to/config.json --skills-dir /path/to/skills --workspace /path/to/ws
```

Explicitly specify a framework to skip auto-detection:

```bash
python3 zhiming.py --framework claude
python3 zhiming.py --framework generic --config /custom/config.json
```

## Adding a New Framework

Add an entry to `SCHEMA_MAP` in `zhiming.py`. Each entry defines:

| Key | Type | Description |
|-----|------|-------------|
| `model_providers_path` | `list[str]` or `None` | Nested key path to providers in config JSON |
| `provider_api_key` | `str` | Provider sub-key for API type |
| `provider_models_key` | `str` | Provider sub-key for model list |
| `model_id_key` | `str` | Model sub-key for ID |
| `skills_entries_path` | `list[str]` or `None` | Key path to skills entries; `None` = not supported |
| `skill_enabled_key` | `str` or `None` | Skill sub-key for enabled flag |
| `channels_path` | `list[str]` or `None` | Key path to channels; `None` = not supported |
| `channel_enabled_key` | `str` or `None` | Channel sub-key for enabled flag |
| `workspace_files` | `list[str]` | Key workspace files to check for existence |

Then add the framework's default paths to `FRAMEWORK_DEFAULTS` (checked in priority order).

Set any path to `None` to skip that scan dimension entirely for the framework.

## Extensions

- **Auto-detection**: Detects OpenClaw, Claude Code, Cline, Continue, Cursor automatically. Falls back to `--config` / `--skills-dir` / `--workspace` for custom setups.
- **Incremental updates**: TOOLS.md is only rewritten when scan results differ from the previous run. Identical runs print "up to date" and skip the write.
- **Atomic writes**: TOOLS.md written via `.tmp` + `os.rename` to avoid partial reads.
- **Concurrent version checks**: All 14 CLI tools version-checked in parallel (ThreadPoolExecutor, 2s timeout).
- **Import-friendly**: `from zhiming import scan_all` for use in other scripts.
- **Pluggable schema**: `SCHEMA_MAP` defines JSON navigation paths per framework, making it trivial to add new Agent frameworks.
- **User content**: Text between `<!-- user:begin -->` and `<!-- user:end -->` is preserved across scans (unless `--force`).

## Security

- API key **names** only — values are never read, logged, or output
- Sensitive directories (.ssh, .aws, .kube, .env files) are excluded
- All results stay local — nothing is sent to external services
- Paths use `~` for home directory

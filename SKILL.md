---
name: zhiming
description: "Scans the local system environment and writes a structured inventory to TOOLS.md, so every new session knows exactly which tools, APIs, models, and skills are available."
---

# ZhiMing (知明) — AI Agent Self-Awareness Toolkit

Scans the local system environment and writes a structured inventory to `TOOLS.md`.

## When to Run

| Trigger | Condition |
|---------|-----------|
| Manual | User says "scan environment", "update tools", "refresh environment", etc. |
| Gap detected | Agent tries to use a tool/API not in TOOLS.md and fails or gets confused |

**Do NOT run:** every session start, timed schedules, or normal task execution.

## Scan Dimensions (7 total)

1. **Search tools**: tvly, mcporter, jina, gh — detected via `command -v`
2. **API keys**: env vars matching `*_API_KEY`, `*_TOKEN`, `*_SECRET` (names only, never values)
3. **Model providers**: parsed from `~/.openclaw/openclaw.json` → `models.providers`, top 3 models each
4. **Installed skills**: scanned from `~/.openclaw/skills/` and `<workspace>/skills/`, description from SKILL.md frontmatter
5. **Communication channels**: from `openclaw.json` → `channels`
6. **CLI toolkit**: git, docker, python3, node, ffmpeg, magick, pandoc, curl, wget, jq, sqlite3, rg, fd, bat — concurrent version checks
7. **Workspace files**: AGENTS.md, SOUL.md, MEMORY.md, TOOLS.md, USER.md, DREAMS.md, IDENTITY.md

## Usage

```bash
python3 ~/.openclaw/skills/zhiming/zhiming.py             # scan + update TOOLS.md
python3 ~/.openclaw/skills/zhiming/zhiming.py --demo      # human-readable summary
python3 ~/.openclaw/skills/zhiming/zhiming.py --json      # raw JSON to stdout
python3 ~/.openclaw/skills/zhiming/zhiming.py --force     # full rebuild (discard user content)
```

Or specify a custom workspace:

```bash
python3 ~/.openclaw/skills/zhiming/zhiming.py --workspace /path/to/ws
```

For non-OpenClaw frameworks, use `--config` and `--skills-dir`:

```bash
python3 ~/.openclaw/skills/zhiming/zhiming.py --config /path/to/config.json --skills-dir /path/to/skills
```

## Extensions

- **Incremental updates**: TOOLS.md is only rewritten when scan results differ from the previous run. Identical runs print "up to date" and skip the write.
- **Atomic writes**: TOOLS.md written via `.tmp` + `os.rename` to avoid partial reads.
- **Concurrent version checks**: All 14 CLI tools version-checked in parallel (ThreadPoolExecutor, 2s timeout).
- **Import-friendly**: `from zhiming import scan_all` for use in other scripts.
- **Configurable paths**: `--config` and `--skills-dir` CLI options for non-OpenClaw frameworks.
- **User content**: Text between `<!-- user:begin -->` and `<!-- user:end -->` is preserved across scans (unless `--force`).

## Security

- API key **names** only — values are never read, logged, or output
- Sensitive directories (.ssh, .aws, .kube, .env files) are excluded
- All results stay local — nothing is sent to external services
- Paths use `~` for home directory

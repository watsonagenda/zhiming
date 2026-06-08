# Detection Matrix

Tool detection reference for the zhiming scanner. Maps each tool/API/provider to its detection method, expected path, and fallback strategies.

## Search & Retrieval Tools

| Tool | CLI Command | Detection | Version Flag | Fallback Detection |
|------|------------|-----------|-------------|-------------------|
| Tavily Search | `tvly` | `command -v tvly` | `tvly --version` | Check `npm list -g @tavily/core` |
| Agent-Reach | `mcporter` | `command -v mcporter` | `mcporter --version` | Check `~/.mcporter/` config dir |
| Jina Reader | `jina` | `command -v jina` | `jina --version` | Check Python `pip show jina` |
| GitHub CLI | `gh` | `command -v gh` | `gh --version` | Check `brew list gh` (macOS) |

## Model Providers

| Provider | Config Source | Key Field | Models Field |
|----------|--------------|-----------|-------------|
| All providers | `~/.openclaw/openclaw.json` | `models.providers.<name>` | `.models[].id` (first 3) |

## Skills

| Detection Path | Config Source | Status Field |
|---------------|--------------|-------------|
| `~/.openclaw/skills/<name>/` | `openclaw.json` → `skills.entries.<name>.enabled` | `true` / `false` |
| `<workspace>/skills/<name>/` | same | same |
| `~/.openclaw/skills/<name>/SKILL.md` | frontmatter `description:` | N/A |

## Communication Channels

| Channel | Config Source | Detection Field |
|---------|--------------|----------------|
| All channels | `~/.openclaw/openclaw.json` | `channels.<name>.enabled` |

## System CLI Tools

| Tool | Detection | Version Command | Version Regex |
|------|-----------|----------------|--------------|
| git | `command -v git` | `git --version` | `(\d+\.\d+\.\d+)` |
| docker | `command -v docker` | `docker --version` | `(\d+\.\d+\.\d+)` |
| python3 | `command -v python3` | `python3 --version` | `(\d+\.\d+\.\d+)` |
| node | `command -v node` | `node --version` | `v(\d+\.\d+\.\d+)` |
| ffmpeg | `command -v ffmpeg` | `ffmpeg -version` | `(\d+\.\d+)` |
| magick | `command -v magick` | `magick --version` | `(\d+\.\d+\.\d+)` |
| pandoc | `command -v pandoc` | `pandoc --version` | `(\d+\.\d+)` |
| curl | `command -v curl` | `curl --version` | `(\d+\.\d+\.\d+)` |
| wget | `command -v wget` | `wget --version` | `(\d+\.\d+\.\d+)` |
| jq | `command -v jq` | `jq --version` | `(\d+\.\d+)` |
| sqlite3 | `command -v sqlite3` | `sqlite3 --version` | `(\d+\.\d+\.\d+)` |
| rg | `command -v rg` | `rg --version` | `(\d+\.\d+\.\d+)` |
| fd | `command -v fd` | `fd --version` | `(\d+\.\d+\.\d+)` |
| bat | `command -v bat` | `bat --version` | `(\d+\.\d+\.\d+)` |

## Workspace Files

| File | Path | Purpose |
|------|------|---------|
| AGENTS.md | `<workspace>/AGENTS.md` | Multi-agent workflows |
| SOUL.md | `<workspace>/SOUL.md` | Behavioral guidelines |
| MEMORY.md | `<workspace>/MEMORY.md` | Long-term memory |
| TOOLS.md | `<workspace>/TOOLS.md` | Tool inventory (this file) |
| USER.md | `<workspace>/USER.md` | User preferences |
| DREAMS.md | `<workspace>/DREAMS.md` | Aspirations/goals |
| IDENTITY.md | `<workspace>/IDENTITY.md` | Agent identity |

## API Key Patterns

| Pattern | Examples |
|---------|---------|
| `*_API_KEY` | `TAVILY_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` |
| `*_TOKEN` | `GITHUB_TOKEN`, `MARVIS_GALILEO_TOKEN` |
| `*_SECRET` | `JWT_SECRET`, `APP_SECRET` |

**Skipped prefixes (internal):** `SECURITY_`, `OAUTH_`, `PRIVATE_`, `CERT_`, `KEYCHAIN_`, `GATEWAY_`

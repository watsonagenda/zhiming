---
name: zhiming
description: "Scans the local system environment and writes a structured inventory to TOOLS.md, so every new session knows exactly which tools, APIs, models, and skills are available."
---

# ZhiMing (知明) — AI Agent Self-Awareness Toolkit

Scans the local system environment and writes a structured inventory to `TOOLS.md`, so every new session knows exactly which tools, APIs, models, and skills are available.

## When to Run

**Trigger (only these two):**

| Trigger | Condition |
|---------|-----------|
| Manual | User says "scan environment", "update tools", "refresh environment", etc. |
| Gap detected | Agent tries to use a tool/API not in TOOLS.md and fails or gets confused |

**Do NOT run on:**
- Every session start
- Timed schedule (daily/hourly)
- Normal task execution
- Installing random software unrelated to agent capabilities

## Scan Dimensions

Run the scan script. It checks these categories:

### 1. Search & Retrieval Tools (Priority-ordered)

Check for these CLI tools in order of search quality:

| Priority | Tool | Detection | CLI Command |
|----------|------|-----------|-------------|
| 1 | Tavily Search | `command -v tvly` | `tvly` |
| 2 | Agent-Reach | `command -v mcporter` | `mcporter` |
| 3 | Jina Reader | `command -v jina` | `jina` |
| 4 | GitHub CLI | `command -v gh` | `gh` |
| 5 | web_fetch (built-in) | Always available | — |
| 6 | web_search (built-in) | Always available | — |

Record which are present, their versions, and any associated API key env vars (name only, never the value).

### 2. API Key Configuration

Check for environment variables matching these patterns:
- `*_API_KEY`
- `*_TOKEN`
- `*_SECRET`

Record only the variable name (e.g. `TAVILY_API_KEY`, `OPENAI_API_KEY`). Never output the actual value. Do not read `.env` files directly — only check if the variable name exists in the current shell environment.

### 3. Model Providers

Parse the agent framework configuration file (typically `~/.openclaw/openclaw.json` or equivalent) to extract:
- Provider name
- Representative models (1-3 per provider, not the full list)
- Model type (main / fallback / embedding / vision / etc.)

Example output row:
```
| NVIDIA NIM | nvidia-nim/baai/bge-m3 (embedding), meta/llama-3.1-70b (fallback) | Embedding + Fallback |
```

### 4. Installed Skills

List all directories under `~/.openclaw/skills/` and also check `workspace/skills/`. For each skill:
- Read the first 5 lines of `SKILL.md` to extract `name` and `description` from YAML frontmatter
- Report path and purpose

Also check framework config for which skills are actually enabled.

### 5. Communication Channels

Parse framework configuration file for channels configuration.

### 6. System CLI Tools

Check for these commonly useful tools:
`git`, `docker`, `python3`, `node`, `ffmpeg`, `imagemagick`, `pandoc`, `curl`, `wget`, `jq`, `sqlite3`

Record path and version for each present one.

### 7. Workspace Files

Check existence of these key files in the active workspace:
`AGENTS.md`, `SOUL.md`, `MEMORY.md`, `TOOLS.md`, `USER.md`, `DREAMS.md`, `IDENTITY.md`

## Output: TOOLS.md Format

Write to the active workspace's `TOOLS.md`. The generated file must follow this structure:

```markdown
# Tools & Environment

> Auto-generated: YYYY-MM-DD HH:MM:SS | zhiming v1.0
> To refresh: say "scan environment"

## Search & Retrieval (Priority ↓)

| Priority | Tool | CLI | Status | API Key | Notes |
|----------|------|-----|--------|---------|-------|
| 1 | Tavily Search | tvly | ✅ | $TAVILY_API_KEY | Web + news search |
| ... | ... | ... | ... | ... | ... |

## Model Providers

| Provider | Representative Models | Role |
|----------|----------------------|------|
| ... | ... | ... |

## Installed Skills

| Skill | Path | Status | Purpose |
|-------|------|--------|---------|
| ... | ... | enabled/disabled | ... |

## CLI Toolkit

| Tool | Path | Version |
|------|------|---------|
| ... | ... | ... |

## Communication Channels

| Channel | Status |
|---------|--------|
| ... | ... |

## Workspace Files

| File | Status |
|------|--------|
| AGENTS.md | present/missing |
| ... | ... |
```

### Ownership & Incremental Update

- **First run**: Full scan, write complete TOOLS.md.
- **Subsequent runs**: Compare new scan results with existing TOOLS.md. Only update sections that changed.
- **User content**: If the user has manually added content between `<!-- user:begin -->` and `<!-- user:end -->` markers, preserve it unchanged.
- **Force rebuild**: If user says "force scan" or "rebuild TOOLS.md", overwrite entirely.

## Scripts

### scan-environment.sh

The main scanning script. Usage:

```bash
bash ~/.openclaw/skills/zhiming/scripts/scan-environment.sh
```

Outputs a JSON object with all scan results to stdout. The JSON structure:

```json
{
  "timestamp": "ISO-8601",
  "workspace": "path/to/active/workspace",
  "search_tools": [...],
  "api_keys": [...],
  "model_providers": [...],
  "skills": [...],
  "channels": [...],
  "cli_tools": [...],
  "workspace_files": [...]
}
```

### update-tools.sh

Consumes the JSON from scan-environment.sh and writes TOOLS.md:

```bash
bash ~/.openclaw/skills/zhiming/scripts/scan-environment.sh | bash ~/.openclaw/skills/zhiming/scripts/update-tools.sh
```

Supports `--workspace <path>` to target a specific workspace.

## Detection Triggers (Gap Detection)

When the agent encounters any of these situations, it should suggest running a scan:

- A tool/CLI command is not found in TOOLS.md
- An API key env var is referenced but not documented
- A model provider is configured but missing from TOOLS.md
- A skill is installed but not listed
- User mentions installing a new tool or configuring a new integration

Response format when a gap is detected:
> I notice that [tool/api/skill] is not in your TOOLS.md. It may be available but undocumented. Would you like me to run an environment scan to update the inventory?

## Security Constraints

- API key values are NEVER read, logged, or output. Only variable names.
- Sensitive directories (`.ssh`, `.aws`, `.kube`, `.env` files) are never scanned.
- All scan results are written to TOOLS.md only — never to external services.
- Paths in output use `~` for home directory to avoid leaking the full username when possible.

## Example Session

```
User: I just installed a new search tool called Exa. Can you update?
Agent: Let me scan your environment and update TOOLS.md.
      [runs scan → writes TOOLS.md]
      Done. TOOLS.md updated. Exa (CLI: exa) added to Search & Retrieval at priority 2.
```

```
Agent: [tries to use mcporter, not in TOOLS.md]
      I notice mcporter (Agent-Reach) is not in your TOOLS.md. It may be available but undocumented.
      Would you like me to run an environment scan?
```

# ZhiMing (知明) — AI Agent Self-Awareness Toolkit

> **知明** (zhī míng): "Know thyself." From the Chinese proverb *自知之明* — the wisdom of knowing oneself.

A lightweight toolkit that scans the local system environment and generates a structured `TOOLS.md` inventory, so AI agents always know exactly which CLI tools, API keys, model providers, skills, and communication channels are available — even in a brand-new session.

## The Problem

AI agents suffer from **session amnesia**. Every time a new chat session starts, the agent has no memory of the tools and capabilities configured in its runtime environment. This leads to:

- **Degraded tool selection**: Falling back to `web_fetch` when Tavily Search is configured and available
- **Wasted API keys**: Paid search APIs sitting unused because the agent doesn't know they exist
- **Repeated setup**: Users having to tell the agent "use Tavily" in every session
- **Capability blindness**: Installed skills, configured model providers, and communication channels go unnoticed

ZhiMing solves this by giving the agent **self-awareness** — a single source of truth about its own runtime capabilities.

## Core Capabilities (7 Scan Dimensions)

| # | Dimension | What It Scans |
|---|-----------|--------------|
| 1 | **Search & Retrieval** | Tavily Search, Agent-Reach, Jina Reader, GitHub CLI — priority-ordered |
| 2 | **API Keys** | Environment variables (`*_API_KEY`, `*_TOKEN`, `*_SECRET`) — names only, never values |
| 3 | **Model Providers** | Configured LLM providers and their representative models |
| 4 | **Installed Skills** | All skills in the framework, with enable/disable status and descriptions |
| 5 | **Communication Channels** | Configured messaging channels (Feishu, WeChat, Telegram, etc.) |
| 6 | **CLI Toolkit** | System tools: git, docker, python3, node, ffmpeg, pandoc, curl, jq, sqlite3... |
| 7 | **Workspace Files** | Key config files: AGENTS.md, SOUL.md, MEMORY.md, TOOLS.md, IDENTITY.md... |

## Installation

### Prerequisites

- Bash 4+
- Python 3.8+
- An AI agent framework that supports skills (e.g., OpenClaw)

### Quick Install

```bash
# Clone the repository into your skills directory
git clone https://github.com/YOUR_USERNAME/zhiming.git ~/.openclaw/skills/zhiming

# Run the first scan
bash ~/.openclaw/skills/zhiming/scripts/scan-environment.sh | \
  bash ~/.openclaw/skills/zhiming/scripts/update-tools.sh
```

Or use the one-liner:

```bash
bash ~/.openclaw/skills/zhiming/run.sh
```

### Verify

After installation, your workspace `TOOLS.md` should be populated with a full environment inventory.

## Usage

### Manual Trigger

Tell your agent any of these:

- "scan environment"
- "update tools"
- "refresh environment"
- "what tools do I have?"

The agent will run the scan and update `TOOLS.md`.

### Passive (Gap Detection)

The agent automatically suggests a scan when it encounters:

- A tool/CLI not listed in TOOLS.md
- An API key referenced but undocumented
- A model provider configured but missing from inventory
- A skill installed but not listed

### Demo Mode

```bash
python3 ~/.openclaw/skills/zhiming/scripts/demo.py
```

Displays a human-friendly summary of scan results without writing files.

## Project Structure

```
zhiming/
├── SKILL.md                    # Main skill instructions for the AI agent
├── README.md                   # This file
├── README_CN.md                # 中文文档
├── REQUIREMENTS.md             # Detailed requirements (Chinese)
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
├── run.sh                      # One-command scan → update
├── assets/
│   └── TOOLS-TEMPLATE.md       # TOOLS.md template structure
├── scripts/
│   ├── scan-environment.sh     # Core scanning script (outputs JSON)
│   ├── update-tools.sh         # JSON → TOOLS.md writer
│   └── demo.py                 # Human-friendly scan summary
└── references/
    └── detection-matrix.md     # Detection methods for each tool/provider
```

## FAQ

**Q: Does this read my API key values?**
A: No. ZhiMing only records environment variable *names* (e.g., `TAVILY_API_KEY`), never their values. It does not read `.env` files or any credential files.

**Q: Does it scan my private directories?**
A: No. Sensitive directories (`.ssh`, `.aws`, `.kube`) are explicitly excluded from all scans.

**Q: Does it run automatically on every session?**
A: No. Scans only run when explicitly triggered by the user or when the agent detects a gap in its tool knowledge.

**Q: Can I add my own notes to TOOLS.md?**
A: Yes. Content between `<!-- user:begin -->` and `<!-- user:end -->` markers is preserved across scans.

**Q: Which AI agent frameworks are supported?**
A: Currently tested with OpenClaw. The scan scripts are framework-agnostic and can be adapted to any agent system that uses a `TOOLS.md` file.

## Security

- API key **names** only — values are never read, logged, or output
- Sensitive directories (`.ssh`, `.aws`, `.kube`, `.env` files) are excluded
- All results stay local — nothing is sent to external services
- Paths use `~` for home directory to avoid leaking usernames

## License

MIT — see [LICENSE](./LICENSE) for details.

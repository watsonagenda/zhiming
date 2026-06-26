# 知明 (ZhiMing) — AI Agent 自感知工具箱

> **知明**：取自"自知之明"——让 AI Agent 拥有对自身能力的清醒认知。

一个轻量级工具，用于扫描本地系统环境并更新结构化的 `TOOLS.md` 清单，让 AI Agent 在每个新会话中都能准确了解其可用的 CLI 工具、API 密钥、模型供应商、技能和通信渠道。

## 要解决的问题

AI Agent 存在**会话失忆**问题。每次新对话开始时，Agent 完全不知道自己的运行环境中配置了哪些工具和能力，导致：

- **工具降级**：明明配置了 Tavily Search，却用低效的 `web_fetch`
- **资源浪费**：付费搜索 API 闲置不用
- **重复沟通**：用户需要在每个会话中说"用 Tavily 搜索"
- **能力盲区**：已安装的技能、配置的模型供应商、通信渠道全部被忽略

知明的解决方案是赋予 Agent **自知之明**——一份关于自身运行时能力的权威清单。

## 核心能力（7 个扫描维度）

| # | 维度 | 扫描内容 |
|---|------|---------|
| 1 | **搜索与检索** | Tavily Search、Agent-Reach、Jina Reader、GitHub CLI（按优先级排序） |
| 2 | **API 密钥** | 环境变量（`*_API_KEY`、`*_TOKEN`、`*_SECRET`）——仅记录名称，不记录值 |
| 3 | **模型供应商** | 已配置的 LLM 供应商及其代表模型 |
| 4 | **已安装技能** | 框架中所有技能，含启用/禁用状态和描述 |
| 5 | **通信渠道** | 已配置的消息渠道（飞书、微信、Telegram 等） |
| 6 | **CLI 工具箱** | 系统工具：git、docker、python3、node、ffmpeg、pandoc、curl、jq、sqlite3... |
| 7 | **工作区文件** | 关键配置文件：AGENTS.md、SOUL.md、MEMORY.md、TOOLS.md、IDENTITY.md... |

## 安装

### 前置条件

- Python 3.8+
- 支持技能的 AI Agent 框架（如 OpenClaw）

### 快速安装

```bash
# 克隆仓库到技能目录
git clone https://github.com/watsonagenda/zhiming.git ~/.openclaw/skills/zhiming

# 将 SKILL.md 复制到 zhiming 技能目录并启用
cp ~/.openclaw/skills/zhiming/SKILL.md ~/.openclaw/skills/zhiming/SKILL.md

# 在配置中启用 zhiming 技能（添加到 skills.entries）：
#   "zhiming": { "enabled": true }

# 运行首次扫描
python3 ~/.openclaw/skills/zhiming/zhiming.py
```

技能启用后，Agent 框架会自动发现 `SKILL.md`。

### 验证

安装完成后，工作区 `TOOLS.md` 应该已填充完整的环境清单。

## 使用方法

### CLI 模式

```bash
python3 ~/.openclaw/skills/zhiming/zhiming.py             # 扫描 + 更新 TOOLS.md
python3 ~/.openclaw/skills/zhiming/zhiming.py --demo      # 人类友好摘要（不写入文件）
python3 ~/.openclaw/skills/zhiming/zhiming.py --json      # 原始 JSON 输出到 stdout
python3 ~/.openclaw/skills/zhiming/zhiming.py --force     # 强制全量重建（丢弃用户内容）

# 指定自定义工作区
python3 ~/.openclaw/skills/zhiming/zhiming.py --workspace /path/to/ws

# 自定义配置 / 技能目录（适配非 OpenClaw 框架）
python3 ~/.openclaw/skills/zhiming/zhiming.py --config /path/to/config.json --skills-dir /path/to/skills
```

### 手动触发（通过 Agent）

告诉 Agent 以下任一指令：

- "扫描环境"
- "更新工具列表"
- "刷新环境信息"
- "我有哪些工具可用？"

Agent 会运行扫描并更新 `TOOLS.md`。

### 被动触发（能力缺口检测）

当 Agent 遇到以下情况时，会自动建议扫描：

- 某个 CLI 工具未在 TOOLS.md 中列出
- 引用了某个 API 密钥但 TOOLS.md 中无记录
- 模型供应商已配置但未在清单中
- 技能已安装但未列出

## 扩展设计

- **增量更新**：仅当扫描结果与上次不同时才重写 TOOLS.md。内容不变时输出"up to date"并跳过写入，有变化时展示差异摘要。
- **原子写入**：TOOLS.md 先写 `.tmp` 临时文件，再通过 `os.rename` 原子替换，防止其他进程读到不完整的文件。
- **并发版本检查**：全部 14 个 CLI 工具（`git`、`docker`、`python3`、`node` 等）的 `--version` 调用通过 `ThreadPoolExecutor` 并发执行（每个 2 秒超时）。最坏情况墙钟时间从 28 秒降至 2 秒。
- **可导入设计**：`scan_all()` 函数设计为可复用：`from zhiming import scan_all`。
- **可配置路径**：`--config` 和 `--skills-dir` CLI 选项解耦扫描器与 OpenClaw 默认值，可适配任何使用 JSON 配置和技能目录的 Agent 框架。
- **面向未来扩展**：每个扫描维度为独立函数。新增维度只需实现一个函数并在 `scan_all()` 中添加一行调用。

## 项目结构

```
zhiming/
├── zhiming.py                  # 单一入口脚本（扫描器 + 更新器 + 演示模式）
├── SKILL.md                    # AI Agent 主技能指令
├── README.md                   # 英文文档
├── README_CN.md                # 本文档（中文）
├── CONTRIBUTING.md             # 贡献指南
├── LICENSE                     # MIT 许可证
├── assets/
│   └── TOOLS-TEMPLATE.md       # TOOLS.md 模板结构
├── references/
│   └── detection-matrix.md     # 各工具/供应商的检测方法矩阵
└── .gitignore
```

> **依赖说明**：扫描器从 JSON 配置文件中读取技能和渠道配置（默认：`~/.openclaw/openclaw.json`）。使用 `--config` 可指向任意框架的等效配置。扫描器本身零 Python 第三方依赖（仅使用标准库）。

## 常见问题

**问：会读取我的 API 密钥值吗？**
答：不会。知明仅记录环境变量*名称*（如 `TAVILY_API_KEY`），绝不读取或输出其值。不读取 `.env` 文件或任何凭据文件。

**问：会扫描我的隐私目录吗？**
答：不会。敏感目录（`.ssh`、`.aws`、`.kube`）被明确排除在所有扫描之外。

**问：每次会话都会自动运行吗？**
答：不会。仅在用户明确触发或 Agent 检测到能力缺口时才运行扫描。

**问：可以在 TOOLS.md 中添加自己的备注吗？**
答：可以。`<!-- user:begin -->` 和 `<!-- user:end -->` 标记之间的内容在扫描时会被保留（除非使用 `--force`）。

**问：支持哪些 AI Agent 框架？**
答：默认适配 OpenClaw，但通过 `--config` 和 `--skills-dir` CLI 选项可适配任何使用 JSON 配置和技能目录的 Agent 框架。扫描逻辑本身完全框架无关。

## 安全

- 仅记录 API 密钥**名称**——绝不读取、记录或输出其值
- 排除敏感目录（`.ssh`、`.aws`、`.kube`、`.env` 文件）
- 所有结果保留在本地——不发送到任何外部服务
- 路径使用 `~` 避免泄露用户名

## 开源协议

MIT — 详见 [LICENSE](./LICENSE)。

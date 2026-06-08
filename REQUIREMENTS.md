# ZhiMing (知明) - 需求文档

## 背景与动机

AI Agent 每次新建会话时，TOOLS.md 是一个空模板，Agent 不知道自己的运行环境中有哪些已配置的 CLI 工具、API key、模型供应商、Skills 等。这导致 Agent 频繁降级使用低效工具（如用 web_fetch 替代已配置的 Tavily Search），无法充分利用已部署的能力。

需要一个技能来自动感知并持久化当前系统环境信息，让 Agent 在每个新会话中都能准确了解自己的工具箱。

## 目标

开发一个 AI Agent 技能，命名为 `zhiming`（知明），核心功能：

1. **自动扫描系统环境**：检测已安装的 CLI 工具、API key 配置、模型供应商、已启用的 Skills、通信渠道等
2. **生成/更新 TOOLS.md**：将扫描结果写入工作区 `TOOLS.md`，替代空模板
3. **增量更新**：支持按需增量更新，而非每次全量重建
4. **自感知能力**：Agent 本身能意识到何时需要刷新环境信息

## 技能结构设计

```
zhiming/
├── SKILL.md                    # 主技能文件（YAML frontmatter + 完整指令）
├── README.md                   # 概述与安装说明
├── assets/                     # 模板与参考文件
│   └── TOOLS-TEMPLATE.md       # TOOLS.md 的模板结构
├── scripts/
│   ├── scan-environment.sh     # 核心扫描脚本
│   ├── update-tools.sh         # 更新 TOOLS.md 的脚本
│   └── demo.py                 # 扫描结果展示
└── references/
    └── detection-matrix.md     # 工具检测矩阵（检测命令、路径、特征）
```

## 功能规格

### 1. 扫描维度

| 维度 | 检测内容 | 检测方式 | 示例 |
|------|---------|---------|------|
| CLI 工具 | 已安装的命令行工具 | `which` / `command -v` | tvly, mcporter, gh, jina |
| 搜索工具链 | 搜索专用工具及其优先级 | 检查 PATH + 版本 | Tavily Search (tvly), Agent-Reach, Jina Reader |
| API Key 配置 | 环境变量中的 API key | `env` + 配置文件扫描 | TAVILY_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY |
| 模型供应商 | 已配置的 LLM 供应商 | 配置文件解析 | Agnes, NVIDIA NIM, Kilo AI, DeepSeek |
| Skills 清单 | 已安装的 Skills | 扫描技能目录 | pdf, xlsx, tavily-search, agent-reach |
| 通信渠道 | 已配置的消息渠道 | 配置文件解析 | 飞书, 微信, Telegram |
| 系统工具 | 系统级可用工具 | `which` 检查 | git, docker, node, python, ffmpeg |
| 工作区文件 | 工作区关键文件 | 文件存在检查 | AGENTS.md, SOUL.md, MEMORY.md |

### 2. TOOLS.md 输出格式

生成的 TOOLS.md 应包含以下区块：

```markdown
# Tools & Environment

> 自动生成于 YYYY-MM-DD HH:MM:SS | 知明 v1.0

## 搜索工具链（优先级从高到低）

| 优先级 | 工具 | CLI 命令 | 状态 | 备注 |
|--------|------|---------|------|------|
| 1 | Tavily Search | tvly | ✅ 已配置 | API key: $TAVILY_API_KEY |
| 2 | Agent-Reach | mcporter | ✅ | 17平台集成 |
| 3 | Jina Reader | jina | ✅ | 网页内容抓取 |
| 4 | GitHub CLI | gh | ✅ | 仓库搜索 |

## 可用的 Skills

| Skill 名称 | 路径 | 用途 |
|-----------|------|------|
| pdf | ~/.openclaw/skills/pdf/ | PDF 文件处理 |
| xlsx | ~/.openclaw/skills/xlsx/ | Excel 文件处理 |
| ... | ... | ... |

## 模型供应商

| 供应商 | 模型 | 类型 |
|--------|------|------|
| Agnes | agnes-v1 | 主模型 |
| NVIDIA NIM | multi-model | 备选 + embedding |
| Kilo AI | ... | 辅助 |

## CLI 工具箱

| 工具 | 路径 | 版本 |
|------|------|------|
| git | /usr/bin/git | 2.39 |
| python | /usr/local/bin/python3 | 3.12 |
| ... | ... | ... |

## 通信渠道

| 渠道 | 状态 | 配置位置 |
|------|------|---------|
| 飞书 | ✅ | ~/.openclaw/channels/feishu |
| ... | ... | ... |
```

### 3. 触发机制

| 触发器 | 场景 | 说明 |
|--------|------|------|
| 手动触发 | 用户说 "扫描环境" / "更新工具列表" / "刷新环境信息" | 主动指令，安装新工具后使用 |
| 发现缺失 | Agent 执行任务时发现某个工具未在 TOOLS.md 中列出 | 被动触发，不额外消耗，仅遇到问题时才跑 |

**明确不触发**：每次会话启动、定时任务、日常对话、执行普通任务——这些场景一律不触发扫描。避免无意义的系统开销。只有用户主动要求或真正遇到工具缺失时才运行。

### 4. 增量更新策略

- 首次运行：全量扫描并生成 TOOLS.md
- 后续运行：对比差异，仅更新变化的部分
- 保留用户手动添加的内容（通过注释标记区块所有权）
- 提供 `--force` 选项强制全量重建

## 技能规范兼容性

遵循 [Agent Skills 规范](https://agentskills.io/specification)：

- SKILL.md 必须包含 YAML frontmatter（`name` 和 `description` 字段）
- `name` 必须与技能文件夹名一致
- 技能文件夹内不应有独立的 README.md（顶层 README 放在技能目录外或根级）
- 使用 `assets/` 存放模板，`scripts/` 存放可执行脚本，`references/` 存放参考文档

## 技术要点

### 扫描脚本（scan-environment.sh）

- 扫描 CLI 工具：遍历预定义的工具列表，用 `command -v` 检查是否存在
- 扫描 API key：读取常用环境变量命名模式（`*_API_KEY`, `*_TOKEN`, `*_SECRET` 等），仅记录变量名不记录值
- 扫描 Skills：列出技能目录下所有子目录，读取各自的 SKILL.md 提取 name/description
- 扫描模型供应商：解析框架配置文件
- 输出 JSON 格式的中间结果，供 update-tools.sh 消费

### 安全约束

- API key 仅记录变量名，严禁输出实际值
- 不读取 `.env` 文件内容，仅检查变量名是否存在
- 不扫描 `.ssh`、`.aws`、`.kube` 等敏感目录
- 扫描结果中的路径脱敏处理

## 开发阶段

| 阶段 | 内容 | 产出物 |
|------|------|--------|
| 阶段 1 | 需求文档（当前） | REQUIREMENTS.md |
| 阶段 2 | SKILL.md 主文件（核心指令） | SKILL.md |
| 阶段 3 | 扫描脚本 | scripts/scan-environment.sh |
| 阶段 4 | TOOLS.md 模板 | assets/TOOLS-TEMPLATE.md |
| 阶段 5 | 集成测试 | 手动触发 → 验证 TOOLS.md 输出 |
| 阶段 6 | 安装与文档 | README.md + 安装脚本 |

## 参考

- Agent Skills 规范：https://agentskills.io/specification

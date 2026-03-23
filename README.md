# AI Quick Starter

[English](#english) | [中文](#中文)

An open, bilingual repository of reusable Claude Code skills for repository engineering, refactoring, research, documentation, automation, and capture workflows.

一个公开的、双语优先的 Claude Code 技能集合仓库，覆盖仓库工程、重构、研究、文档、自动化与桌面采集等工作流。

## 中文

### 这是什么

`ai-quick-starter` 是一个面向 Claude Code / 类 Claude 插件生态的技能仓库。仓库根目录本身可以作为一个 Claude 插件使用，并通过 `.claude-plugin/marketplace.json` 作为公开市场入口分发。

它不是单一应用，而是一组可复用的 skill 模块。每个技能通常围绕一个明确任务组织，常见内容包括：

- `SKILL.md`：技能说明与触发条件
- `agents/`：配套 agent 合同
- `references/`：稳定参考资料
- `scripts/`：可重复执行的辅助脚本
- `tests/`：脚本或结构化输出的验证
- `assets/` / `artifacts/`：示例资产或产出

### 适合谁

- 想为 Claude Code 搭建公开技能集合的人
- 想复用现成技能来加速仓库分析、修复、重构或文档工作的团队
- 想学习如何组织技能目录、插件清单和市场元数据的维护者

### 快速开始

#### 1. 克隆仓库

仓库当前包含一个子模块路径 `skills/stock-analyzer-skill`，建议递归克隆：

```bash
git clone --recurse-submodules https://github.com/AstroAir/ai-quick-starter.git
cd ai-quick-starter
```

如果你已经克隆过仓库：

```bash
git submodule update --init --recursive
```

#### 2. 作为本地插件测试

Claude Code 官方文档支持直接从本地目录加载插件：

```bash
claude --plugin-dir .
```

加载后，仓库中的技能会以 `ai-quick-starter:<skill-name>` 的命名空间暴露。

#### 3. 作为公开市场安装

根据 Claude Code 官方市场文档，GitHub 仓库可直接作为 marketplace source：

```text
/plugin marketplace add AstroAir/ai-quick-starter
/plugin install ai-quick-starter@astroair-skills
```

当前市场名：`astroair-skills`
当前插件名：`ai-quick-starter`

### 仓库结构

```text
.
├── .claude-plugin/          # Claude 插件与 marketplace 元数据
├── .github/                 # Issue / PR 模板
├── skills/                  # 技能集合
├── CHANGELOG.md             # 版本记录
├── CONTRIBUTING.md          # 贡献指南
├── LICENSE                  # MIT 许可证
├── README.md                # 双语仓库入口
├── SECURITY.md             # 安全报告说明
└── SUPPORT.md              # 支持说明
```

### 技能目录概览

#### 仓库工程与质量

| Skill | 用途 |
| --- | --- |
| `build-project-fixer` | 从真实构建链路出发定位并修复仓库构建/验证问题 |
| `commit-quality-fixer` | 发现并修复阻塞提交的质量门禁 |
| `configuring-commit-checks` | 检测和配置 commit hook / pre-commit 工作流 |
| `gitignore-curator` | 保守地整理 `.gitignore` 与相关 ignore 文件 |
| `codebase-indexing-assistant` | 为大型仓库生成结构索引和阅读入口 |
| `feature-call-chain-mapper` | 追踪功能从入口到跨模块交接的调用链 |
| `project-ai-context-initializer` | 为仓库生成 AI 协作文档与导航上下文 |
| `project-structure-migrator` | 规划和执行项目结构迁移 |
| `project-prompt-optimizer` | 面向项目提示词优化，当前仍需进一步完善说明 |

#### 代码重构与产出生成

| Skill | 用途 |
| --- | --- |
| `component-unit-test-completer` | 为 UI 组件补齐一一对应的单元测试 |
| `python-component-splitter` | 拆分大型 Python 模块 |
| `react-component-splitter` | 拆分大型 React / Next.js 组件 |
| `cpp-teaching-code-generator` | 生成教学用 C++ 示例与练习代码 |
| `draw-mermaid-diagrams` | 生成或修复 Mermaid 图表 |
| `fumadocs-ui-css-design` | 构建或定制 Fumadocs 文档站 |
| `agent-tool-benchmark-builder` | 设计和构建 agent 工具评测集 |
| `agents-team-builder` | 为复杂任务生成 agent 团队方案与草稿配置 |

#### 研究、资讯与数据

| Skill | 用途 |
| --- | --- |
| `ai-news-realtime-multisource` | 多源聚合最新 AI 新闻 |
| `daily-news-multisource-brief` | 生成跨区域日度新闻简报 |
| `china-exchange-daily-brief` | 聚合中国主要交易所最新动态 |
| `stock-analyzer-skill` | 面向 A/H/美股等市场的综合股票分析 |

#### 调试与桌面采集

| Skill | 用途 |
| --- | --- |
| `pua-debugging` | 在 agent 多次失败或陷入被动态时强制提升推进强度 |
| `screenshot` | 采集桌面、窗口或区域截图 |
| `screen-recorder` | 录制桌面或复现视频 |

### 贡献与维护

- 提交前请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)
- 如需报告安全问题，请阅读 [SECURITY.md](SECURITY.md)
- 如需使用帮助或分流说明，请阅读 [SUPPORT.md](SUPPORT.md)

### 说明与边界

- 这个仓库优先服务于公开可分发的技能集合，不保证每个技能都适合作为通用生产方案直接使用。
- 某些技能会依赖 Python、Node.js、`uv`、网络访问或第三方站点，具体依赖请看各技能自己的 `SKILL.md` 与脚本说明。
- `skills/stock-analyzer-skill` 当前通过子模块路径接入，使用前请确保已经初始化子模块。

## English

### What This Repository Is

`ai-quick-starter` is a public, bilingual-first Claude Code skills collection. The repository root can be used as a Claude plugin, and it also exposes a marketplace catalog through `.claude-plugin/marketplace.json`.

This is not a single application. It is a curated set of reusable task-focused skills. Each skill usually includes:

- `SKILL.md` for behavior and trigger guidance
- `agents/` for companion agent contracts
- `references/` for stable supporting material
- `scripts/` for repeatable automation
- `tests/` for helper-script verification
- `assets/` or `artifacts/` for examples and generated outputs

### Who This Is For

- Maintainers building a public Claude Code skills repository
- Teams that want reusable skills for repo analysis, repair, refactoring, and documentation work
- Contributors who want a real example of plugin packaging plus marketplace metadata

### Quick Start

#### 1. Clone The Repository

This repository currently includes a submodule-backed path at `skills/stock-analyzer-skill`, so recursive clone is recommended:

```bash
git clone --recurse-submodules https://github.com/AstroAir/ai-quick-starter.git
cd ai-quick-starter
```

If you already cloned the repository:

```bash
git submodule update --init --recursive
```

#### 2. Test As A Local Plugin

Claude Code supports loading a plugin directly from a local directory:

```bash
claude --plugin-dir .
```

Once loaded, skills are exposed under the `ai-quick-starter:<skill-name>` namespace.

#### 3. Install Through A Marketplace

Based on the official Claude Code marketplace docs, GitHub repositories can be added directly as marketplace sources:

```text
/plugin marketplace add AstroAir/ai-quick-starter
/plugin install ai-quick-starter@astroair-skills
```

Current marketplace name: `astroair-skills`
Current plugin name: `ai-quick-starter`

### Repository Layout

```text
.
├── .claude-plugin/          # Claude plugin and marketplace metadata
├── .github/                 # Issue and pull request templates
├── skills/                  # Reusable skill modules
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Contribution guide
├── LICENSE                  # MIT license
├── README.md                # Bilingual landing page
├── SECURITY.md              # Security reporting guidance
└── SUPPORT.md               # Support routing
```

### Skill Catalog

#### Repository Engineering And Quality

| Skill | Summary |
| --- | --- |
| `build-project-fixer` | Reproduce and repair real repository build or verification failures |
| `commit-quality-fixer` | Fix quality gates that block commits |
| `configuring-commit-checks` | Detect and configure commit-hook or pre-commit setups |
| `gitignore-curator` | Curate `.gitignore` and related ignore rules conservatively |
| `codebase-indexing-assistant` | Build repo indexes and reading maps for unfamiliar codebases |
| `feature-call-chain-mapper` | Trace feature entrypoints and cross-module handoffs |
| `project-ai-context-initializer` | Generate AI-facing repository context docs |
| `project-structure-migrator` | Plan and guide project-structure migrations |
| `project-prompt-optimizer` | Prompt optimization skill that still needs fuller repository-specific polish |

#### Refactoring And Output Generation

| Skill | Summary |
| --- | --- |
| `component-unit-test-completer` | Fill in one-to-one component unit tests |
| `python-component-splitter` | Split oversized Python modules |
| `react-component-splitter` | Split oversized React or Next.js components |
| `cpp-teaching-code-generator` | Generate instructional C++ code and exercises |
| `draw-mermaid-diagrams` | Create or repair Mermaid diagrams |
| `fumadocs-ui-css-design` | Build or customize Fumadocs sites |
| `agent-tool-benchmark-builder` | Build benchmark suites for tool-using agents |
| `agents-team-builder` | Generate agent-team plans and draft configs |

#### Research, News, And Data

| Skill | Summary |
| --- | --- |
| `ai-news-realtime-multisource` | Aggregate the latest AI news from multiple sources |
| `daily-news-multisource-brief` | Produce cross-region daily news briefs |
| `china-exchange-daily-brief` | Summarize major China exchange updates |
| `stock-analyzer-skill` | Analyze stocks across China, Hong Kong, and US markets |

#### Debugging And Desktop Capture

| Skill | Summary |
| --- | --- |
| `pua-debugging` | Force higher-agency debugging behavior when an agent stalls repeatedly |
| `screenshot` | Capture desktop, window, or region screenshots |
| `screen-recorder` | Record repro videos and desktop flows |

### Contributing And Maintenance

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR
- Review [SECURITY.md](SECURITY.md) for vulnerability reporting
- Use [SUPPORT.md](SUPPORT.md) for support routing and expectations

### Notes And Boundaries

- This repository is optimized as a public, distributable skills collection, not as a guarantee that every skill is production-ready for every environment.
- Some skills depend on Python, Node.js, `uv`, network access, or third-party services. Check each skill's own `SKILL.md` and helper scripts for exact requirements.
- `skills/stock-analyzer-skill` is currently linked through a submodule-backed path, so initialize submodules before relying on it.

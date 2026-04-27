# AI Quick Starter — 中文文档

[English](README.md) | 中文

一个公开的、双语优先的 Claude Code 技能集合仓库，覆盖仓库工程、重构、研究、文档、自动化与桌面采集等工作流。

## 这是什么

`ai-quick-starter` 是一个面向 Claude Code / 类 Claude 插件生态的技能仓库。仓库根目录本身可以作为一个 Claude 插件使用，并通过 `.claude-plugin/marketplace.json` 作为公开市场入口分发。

公开市场会同时暴露：

- 一个完整打包插件：`ai-quick-starter`
- 多个可单独安装的 skill 插件：例如 `screenshot`、`build-project-fixer`、`stock-analyzer-skill`

它不是单一应用，而是一组可复用的 skill 模块。每个技能通常围绕一个明确任务组织，常见内容包括：

- `SKILL.md`：技能说明与触发条件
- `agents/`：配套 agent 合同
- `references/`：稳定参考资料
- `scripts/`：可重复执行的辅助脚本
- `tests/`：脚本或结构化输出的验证
- `assets/` / `artifacts/`：示例资产或产出

## 适合谁

- 想为 Claude Code 搭建公开技能集合的人
- 想复用现成技能来加速仓库分析、修复、重构或文档工作的团队
- 想学习如何组织技能目录、插件清单和市场元数据的维护者

## 快速开始

### 1. 克隆仓库

直接正常克隆即可，`skills/stock-analyzer-skill` 现在作为仓库内普通目录维护：

```bash
git clone https://github.com/AstroAir/ai-quick-starter.git
cd ai-quick-starter
```

### 2. 作为本地插件测试

Claude Code 官方文档支持直接从本地目录加载插件：

```bash
claude --plugin-dir .
```

加载后，仓库中的技能会以 `ai-quick-starter:<skill-name>` 的命名空间暴露。

### 3. 作为公开市场安装

根据 Claude Code 官方市场文档，GitHub 仓库可直接作为 marketplace source：

```text
/plugin marketplace add AstroAir/ai-quick-starter
/plugin install screenshot@astroair-skills
```

如果你想一次安装整套技能，也可以继续安装 bundle：

```text
/plugin install ai-quick-starter@astroair-skills
```

当前市场名：`astroair-skills`
当前完整插件名：`ai-quick-starter`
当前 skill 插件名：对应各自 skill 目录名，例如 `screenshot`

## 仓库结构

```text
.
├── .claude-plugin/          # Claude 插件与 marketplace 元数据
├── .github/                 # Issue / PR 模板
├── codex/                   # Codex 配置与主题
├── plugins/                 # 由脚本生成的独立 Claude 插件包装层（默认 link，不复制 skill 内容）
├── skills/                  # 技能集合源码
├── CHANGELOG.md             # 版本记录
├── CONTRIBUTING.md          # 贡献指南
├── LICENSE                  # MIT 许可证
├── README.md                # 双语仓库入口
├── README_zh.md             # 中文独立文档（本文件）
├── SECURITY.md              # 安全报告说明
└── SUPPORT.md               # 支持说明
```

## 技能目录概览

### 仓库工程与质量

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
| `project-prompt-optimizer` | 面向项目提示词优化 |
| `build-debug-script-generator` | 生成构建与调试辅助脚本 |
| `component-library-migrator` | 规划和执行组件库迁移审计 |
| `component-reorg-executor` | 执行组件重组计划 |
| `component-reorg-planner` | 规划组件目录重组方案 |
| `component-unit-test-completer` | 为 UI 组件补齐一一对应的单元测试 |
| `e2e-test-completer` | 同步并修复 Playwright / Cypress E2E 测试 |
| `github-actions-ci-builder` | 构建和调优 GitHub Actions CI 工作流 |
| `local-ci-fixer` | 本地复现和修复 GitHub Actions CI 故障 |
| `project-architecture-design-analyzer` | 分析项目架构设计并提出改进建议 |
| `project-docs-sync` | 同步项目文档与最新代码实现 |
| `project-optimization-opportunity-auditor` | 审计项目优化机会并生成改进计划 |
| `project-skill-builder` | 为特定项目构建定制化技能 |
| `rust-lint-fixer` | 修复 Rust 代码的 lint 和格式化问题 |
| `skill-safety-auditor` | 审计技能的安全性与合规性 |
| `spec-driven-develop` | 大型重构或迁移的规范驱动开发工作流 |
| `openspec-change-cleaner` | 审计和清理 OpenSpec 变更记录 |
| `split-commit-fixer` | 将大体积工作区拆分为可审查的提交批次，逐批修复质量门禁，并将检查点提交整合为干净历史 |

### 代码重构与产出生成

| Skill | 用途 |
| --- | --- |
| `code-simplifier` | 在不改变行为的前提下精简最近改动代码 |
| `python-component-splitter` | 拆分大型 Python 模块 |
| `react-component-splitter` | 拆分大型 React / Next.js 组件 |
| `cpp-teaching-code-generator` | 生成教学用 C++ 示例与练习代码 |
| `draw-mermaid-diagrams` | 生成或修复 Mermaid 图表 |
| `fumadocs-ui-css-design` | 构建或定制 Fumadocs 文档站 |
| `agent-tool-benchmark-builder` | 设计和构建 agent 工具评测集 |
| `agents-team-builder` | 为复杂任务生成 agent 团队方案与草稿配置 |
| `create-mcp-server` | 从零搭建 MCP (Model Context Protocol) 服务器 |
| `design-md` | 为 Stitch 项目生成 DESIGN.md 设计系统文档 |
| `develop-react-flow-projects` | 开发 React Flow 流程图项目 |
| `development-task-orchestrator` | 编排开发任务的执行顺序与依赖关系 |
| `firefly-blog-framework-assistant` | Firefly 博客框架的配置、定制与部署 |
| `image-to-terminal-pixel-art` | 将图片转为终端像素艺术预览 |
| `ink-cli` | 使用 Ink 构建终端 CLI 应用 |
| `ink-expert` | Ink v6 生产级 CLI 开发与迁移 |
| `pdf-reading-workflow` | PDF 文档阅读与结构化提取工作流 |
| `pig-skill-master` | 从 QQ 群聊记录生成可复用的朋友人格技能 |
| `pptx-generator` | 生成 PowerPoint 演示文稿 |
| `react-components` | 将 Stitch 设计转换为模块化 React 组件 |
| `remotion` | 使用 Remotion 将 Stitch 设计转为演示视频 |
| `shadcn-ui` | 使用和维护 shadcn/ui 组件库 |
| `software-research-tutorial-builder` | 构建基于证据的软件研究教程 |
| `stitch-design` | Stitch 设计工作流：提示增强、设计系统与屏幕生成 |
| `stitch-loop` | Stitch 迭代式网站生成与自主构建循环 |
| `taste-design` | 生成 Stitch 高级 DESIGN.md 品味系统 |
| `tauri-rust-component-splitter` | 拆分大型 Tauri + Rust 组件 |
| `tauri-v2` | Tauri v2 桌面/移动端应用开发 |
| `vscode-extension-expert` | VS Code 扩展开发、调试与发布 |

### 研究、资讯与数据

| Skill | 用途 |
| --- | --- |
| `ai-news-realtime-multisource` | 多源聚合最新 AI 新闻 |
| `daily-news-multisource-brief` | 生成跨区域日度新闻简报 |
| `china-exchange-daily-brief` | 聚合中国主要交易所最新动态 |
| `stock-analyzer-skill` | 面向 A/H/美股等市场的综合股票分析 |
| `ai-research-writing` | AI 辅助的研究写作与内容生成 |
| `market-research-skill` | 结构化市场研究与竞品分析 |

### 调试与桌面采集

| Skill | 用途 |
| --- | --- |
| `pua-debugging` | 在 agent 多次失败或陷入被动态时强制提升推进强度 |
| `screenshot` | 采集桌面、窗口或区域截图 |
| `screen-recorder` | 录制桌面或复现视频 |
| `vision-analysis` | 视觉分析与图像内容理解 |

### 系统运维与基础设施

| Skill | 用途 |
| --- | --- |
| `configuring-k8s` | 检查、编辑和验证 Kubernetes 配置 |
| `integrating-redis-into-existing-projects` | 在现有项目中集成 Redis 缓存/队列/限流 |
| `redis-maintenance-script-builder` | 生成 Redis 运维诊断与维护脚本 |
| `writing-safe-shell-commands` | 生成和加固安全的跨平台 shell 命令 |
| `powershell-terminal-config-sync` | 同步 PowerShell 和 Windows Terminal 配置 |
| `powershell-writing-assistant` | 编写和重构生产级 PowerShell 脚本 |
| `fetch-skill-main` | 抓取网页、提取元数据、批量下载内容 |
| `postgres-sql-writer` | 编写和审查 PostgreSQL SQL/DDL/DML |
| `local-javascript-scripting` | 编写本地 Node.js/JavaScript 自动化脚本 |

### 质量门禁与规范优化

| Skill | 用途 |
| --- | --- |
| `guarded-code-comment-editor` | 在保持本地风格的前提下编辑代码注释 |
| `guarded-component-i18n-fix` | 审计和修复组件级国际化问题 |
| `guarded-log-editor` | 在保持约定前提下增删改日志 |
| `guarded-project-i18n-support` | 为项目规划和添加国际化支持 |
| `feature-gap-requirements-auditor` | 对比文档与实现，发现功能缺口 |
| `feature-optimization-planner` | 审计特定模块并生成优化计划 |
| `enhance-prompt` | 将模糊的 UI 生成请求优化为结构化提示词 |
| `session-context-optimizer` | 从本地技能构建精简的会话上下文包 |
| `wave-orchestration` | 大规模任务的迭代式并行 agent 编排 |
| `autonomous-loops` | 自主 agent 循环与无人值守工作流 |
| `vengeful-ghost-skill` | 检测并阻止将真实同事克隆为 AI 替身 |

## Marketplace 生成

独立插件目录 `plugins/` 和 marketplace 清单由脚本生成，不建议手工逐个维护。

`skills/` 是标准 skills CLI 与仓库维护时的唯一事实源。默认生成模式会在 `plugins/` 下创建 link/junction 包装层，让 Claude marketplace 能识别独立插件，同时避免把每个 skill 再复制一份。

如在 `skills/` 下新增或调整技能后需要刷新公开市场内容，可运行：

```bash
uv run --python 3.11 scripts/build_marketplace_plugins.py --repo-root .
```

如果你需要生成一个真实复制文件的发布快照，例如用于单独发布 marketplace 包，可显式使用：

```bash
uv run --python 3.11 scripts/build_marketplace_plugins.py --repo-root . --materialize copy
```

> 注：`scripts/build_marketplace_plugins.py` 当前在仓库中尚未提供，相关功能正在规划中。如需手动维护 `plugins/` 或 marketplace 清单，请参考 `.claude-plugin/marketplace.json` 的格式直接编辑。

## 贡献与维护

- 提交前请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)
- 如需报告安全问题，请阅读 [SECURITY.md](SECURITY.md)
- 如需使用帮助或分流说明，请阅读 [SUPPORT.md](SUPPORT.md)

## 说明与边界

- 这个仓库优先服务于公开可分发的技能集合，不保证每个技能都适合作为通用生产方案直接使用。
- 某些技能会依赖 Python、Node.js、`uv`、网络访问或第三方站点，具体依赖请看各技能自己的 `SKILL.md` 与脚本说明。
- `skills/stock-analyzer-skill` 当前作为仓库内普通技能目录维护，不再依赖子模块初始化。

# Contributing / 贡献指南

Thank you for helping improve `ai-quick-starter`.

感谢你参与完善 `ai-quick-starter`。

## What This Repository Accepts / 仓库接受什么样的贡献

- New Claude Code skills with a clear purpose and a realistic workflow
- Improvements to existing skills, references, scripts, and tests
- Documentation, marketplace metadata, and repository-health improvements
- Bug fixes for helper scripts, examples, and packaging details

- 具有明确用途和真实工作流的新技能
- 对现有技能、参考资料、脚本和测试的改进
- 文档、市场元数据和仓库健康度相关改进
- 辅助脚本、示例和分发细节的修复

## Before You Start / 开始前

1. Read the root [README.md](README.md).
2. Check whether a similar skill already exists under `skills/`.
3. Open an issue first for large additions, restructuring, or marketplace metadata changes.
4. If your change touches `skills/stock-analyzer-skill`, treat it like any other first-party skill directory in this repository.

1. 先阅读根目录的 [README.md](README.md)。
2. 先确认 `skills/` 下是否已经有相似能力。
3. 如果是大型新增、结构调整或市场元数据变更，优先先开 issue。
4. 如果修改 `skills/stock-analyzer-skill`，按仓库内普通一方技能目录处理即可。

## Skill Contribution Checklist / 技能贡献检查清单

For a new skill, try to include:

- `skills/<skill-name>/SKILL.md`
- `skills/<skill-name>/agents/openai.yaml` when the skill uses a dedicated agent contract
- `references/` for stable guidance
- `scripts/` for repeatable automation when the workflow is scriptable
- `tests/` when scripts or structured outputs need verification
- Example assets only when they help users understand or validate the skill

新增技能时，建议尽量包含：

- `skills/<skill-name>/SKILL.md`
- 当技能需要专用 agent 合同时，补 `skills/<skill-name>/agents/openai.yaml`
- `references/` 存放稳定参考资料
- 如果流程可脚本化，补 `scripts/`
- 如果脚本或结构化输出需要验证，补 `tests/`
- 只有在确实帮助理解或验证时再加入示例资产

## Writing Guidance / 编写约定

- Prefer bilingual docs when the content is public-facing.
- Keep skill descriptions specific: explain when to use the skill and when not to use it.
- Prefer small, testable helper scripts over long copy-paste instructions.
- Do not commit secrets, tokens, cookies, or personal local settings.
- Keep generated caches and local tooling output out of git.

- 面向公开读者的内容优先双语。
- 技能描述要具体，说明什么时候该用、什么时候不该用。
- 尽量使用可重复的小脚本，而不是超长手工说明。
- 不要提交密钥、令牌、Cookie 或本地私有设置。
- 不要把缓存和本地产物提交进仓库。

## Pull Request Expectations / PR 要求

- Use a focused branch or a focused commit series.
- Explain the problem, the change, and how you verified it.
- Include screenshots or output samples only when they materially help review.
- Update `README.md`, `CHANGELOG.md`, or marketplace metadata when user-facing behavior changes.

- 使用聚焦的分支或聚焦的提交序列。
- 说明问题、改动内容和验证方式。
- 只有在确实帮助评审时才附截图或输出示例。
- 当用户可见行为变化时，同步更新 `README.md`、`CHANGELOG.md` 或市场元数据。

## Suggested Verification / 建议验证

- Read changed Markdown files for broken headings, stale links, and formatting drift
- Parse JSON files after editing
- Run relevant tests when you change scripts
- Check `git status --short` before opening a PR

- 通读改动过的 Markdown，检查标题、链接和格式是否异常
- 修改 JSON 后做语法解析
- 改脚本时运行对应测试
- 提交 PR 前先看一遍 `git status --short`

## Communication / 沟通方式

- Be concrete and kind.
- Prefer small, reviewable changes over broad rewrites.
- If you are unsure about a repo-wide decision, explain the tradeoff in the PR.

- 保持具体、友善。
- 优先做小而可评审的修改，避免无关大改。
- 如果你对仓库级决策不确定，请在 PR 中把取舍写清楚。

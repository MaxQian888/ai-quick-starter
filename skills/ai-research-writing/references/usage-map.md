# AI Research Writing Usage Map

Use `scripts/select_workflow.py` first when the user gives a broad request and the exact writing path is not obvious.

## Prompt Families

- `cn-to-en`: use the upstream `中转英` section for Chinese-to-English academic translation with LaTeX preservation.
- `en-to-cn`: use `英转中` when the user wants faithful Chinese translation of English LaTeX.
- `zh-refine`: use `中转中`, `表达润色（中文论文）`, or `去 AI 味（Word 中文）` for Chinese rewriting, Word-friendly polishing, or de-AI cleanup.
- `en-refine`: use `表达润色（英文论文）`, `去 AI 味（LaTeX 英文）`, `缩写`, `扩写`, or `逻辑检查` for English polishing and logic review.
- `visual-support`: use `论文架构图`, `实验绘图推荐`, `生成图的标题`, `生成表的标题`, or `实验分析` for figures, tables, and results analysis.
- `reviewer-audit`: use `论文整体以 Reviewer 视角进行审视` when the user wants a harsh review report and revision strategy.
- `skills-setup`: use the setup path when the user asks to configure OpenSkills or install external writing-related skills.

## Basic Workflow

1. Run `python scripts/select_workflow.py --json "<user request>"`.
2. Read the matching section from `references/cache/upstream-awesome-ai-research-writing.md`.
3. If the request is about setup or external skills, also read `references/components-and-setup.md`.
4. Keep outputs aligned to the upstream section's output contract instead of improvising a new format.

## Cache Policy

- Refresh `references/cache/upstream-awesome-ai-research-writing.md` and `references/cache/upstream-section-index.json` with `python scripts/sync_upstream_reference.py` when the upstream source may have changed.
- Treat the cached README as the complete source-of-truth snapshot for prompt wording and section titles.

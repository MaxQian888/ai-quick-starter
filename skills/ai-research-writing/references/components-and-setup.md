# Components And Setup

This skill bundles the local routing and installation logic for the external ecosystem referenced by the upstream repository.

## Curated Components

- `openskills`: OpenSkills CLI used to install GitHub-hosted skills. Prerequisites: Node.js 20.6+ and Git.
- `20-ml-paper-writing`: conference-oriented writing workflow from `zechenzhangAGI/AI-research-SKILLs`.
- `humanizer`: writing naturalization skill from `blader/humanizer`.
- `docx`: Word document creation and editing workflow from `anthropics/skills`.
- `doc-coauthoring`: staged document collaboration workflow from `anthropics/skills`.
- `canvas-design`: figure and diagram design workflow from `anthropics/skills`.

## Installation Rules

1. Build the plan with `python scripts/install_components.py --json all` or a focused component list.
2. Read the generated commands and selectors before executing anything.
3. Use `--execute` only when the user explicitly wants the environment modified.
4. For `anthropics/skills`, select only the requested skills from the interactive installer.

## Verification

- Check `node --version` and `git --version` before relying on OpenSkills.
- Check `npx openskills --version` after install.
- In Cursor-like tooling, confirm the discovered skills under `.claude/skills/` or `.cursor/skills/` and verify the matching skill names are visible.

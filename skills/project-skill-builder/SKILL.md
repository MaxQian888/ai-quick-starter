---
name: project-skill-builder
description: |
  Use whenever you need to analyze an existing repository and scaffold a reusable project-specific skill package for repeated future sessions. Make sure to use this skill whenever the user says "create a skill for this repo", "onboarding docs", "repo-specific skill", "project context", "CLAUDE.md for this project", or "make this easier to work with next time" — even for small projects that are visited frequently. Also trigger when a repository has unique conventions, custom build steps, or tribal knowledge that should be captured for future AI sessions. Covers skill generation, project mapping, working rules extraction, and durable navigation docs.
---

# Project Skill Builder

## Overview

Scan a repository first, then materialize the findings as a small skill package that future Codex runs can reuse.

Default to generating a doc-backed project skill with a strong `SKILL.md`, `CLAUDE.md`, UI metadata, and focused reference files. Treat the generated skill as a starting point that should reflect observed repository truth, not generic boilerplate.

## Adaptive Detection

Before building a skill, detect repository signals:

1. **Project type**: Identify the primary language, framework, and runtime from manifests.
2. **Workspace structure**: Check for monorepo, multi-package, or single-package layout.
3. **Documentation state**: Note existing `README.md`, `CLAUDE.md`, `docs/`, or `ARCHITECTURE.md`.
4. **Build surface**: Identify how to build, test, lint, and run the project.
5. **Team conventions**: Look for style guides, naming conventions, and folder organization patterns.

Use these signals to decide what belongs in the generated skill and what can be left out.

## Workflow

1. Confirm the target repository root and choose a concise skill name for the generated package.
2. Run the helper script:

```bash
python scripts/build_project_skill.py --project-root <repo> --skill-name <skill-name> --output-dir <dir>
```

3. Add `--include` or `--exclude` before widening the scan when the repository is large.
4. Add `--force` only when you intentionally want to replace an existing generated package of the same name.
5. Read `references/scaffolding-workflow.md` before changing script options or widening the scan.
6. Read `references/generated-skill-contract.md` before approving the generated package as ready for reuse.
7. Review the generated `CLAUDE.md`, then `references/project-map.md`, then `references/working-rules.md`.
8. Tighten the generated `SKILL.md` if the repository has special workflows, strong guardrails, or naming language that the first pass missed.
9. Keep observed facts separate from heuristics when you present the result.

## What The Script Generates

The helper creates a new skill directory with:

- `SKILL.md`
- `CLAUDE.md`
- `agents/openai.yaml`
- `references/project-map.md`
- `references/working-rules.md`
- `artifacts/project-analysis.json`

The generated package is intentionally lightweight. It favors repository-specific guidance over speculative automation.

## Examples

### Example 1: Generate a skill for a React monorepo

```bash
python scripts/build_project_skill.py --project-root . --skill-name acme-web --output-dir ./skills
```

### Example 2: Regenerate with narrowed scope

```bash
python scripts/build_project_skill.py --project-root . --skill-name acme-web --output-dir ./skills --include apps/web --include packages/ui --force
```

## Guardrails

- Do not invent commands when the repository already exposes manifest or task-runner truth.
- Do not claim the generated command hints work unless they were executed separately.
- Do not let one broad scan substitute for targeted file reading when the user asks about one subsystem.
- Do not include cache, vendor, temp, or generated directories unless the current task explicitly needs them.
- Do not overfit the generated skill to one transient task. Capture stable repository guidance that will still help in later sessions.
- Do not overwrite an existing generated package unless `--force` is explicit.

## References

- Read `references/scaffolding-workflow.md` for input selection, scan scope, overwrite rules, and post-generation review.
- Read `references/generated-skill-contract.md` for the files, sections, and evidence quality the generated skill should contain.

## Helper Script

Run:

```bash
python scripts/build_project_skill.py --project-root <repo> --skill-name <skill-name> --output-dir <dir>
```

Use `--include` and `--exclude` to narrow the scan when the repository is large or when one package matters more than the rest.

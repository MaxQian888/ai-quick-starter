---
name: project-prompt-optimizer
description: |
  Use whenever you need to generate or optimize execution prompts using repository-specific structure, constraints, and validation workflows. Make sure to use this skill whenever the user asks for a "better prompt", "prompt engineering", "execution prompt", "task prompt", "agent prompt", or "improve this instruction" — especially when the prompt must be run against a real codebase. Also trigger when converting vague task descriptions into actionable instructions, adding verification steps to prompts, or tailoring generic prompts to a specific project's conventions. Covers prompt generation from scratch, prompt optimization from drafts, and repository-aware prompt hardening.
---

# Project Prompt Optimizer

## Overview

Turn a vague task or draft prompt into a repository-aware execution prompt that another agent can run directly.

This skill focuses on prompt quality for real codebases: boundaries, constraints, validation, and deliverables.

## Adaptive Detection

Before optimizing, detect the project context:

1. **Repository structure**: Check for monorepo vs single package, framework, and language stack.
2. **Existing conventions**: Look for `CLAUDE.md`, `CONTRIBUTING.md`, or style guides.
3. **Build and test**: Identify how the project validates changes (lint, typecheck, tests, CI).
4. **Task type**: Determine if the prompt is for coding, refactoring, documentation, or infrastructure.
5. **Target audience**: Note if the prompt is for a human developer, an AI agent, or a CI pipeline.

Use these signals to anchor constraints and validation steps in the final prompt.

## Workflow

1. Classify request type:
   - prompt generation from a task, or
   - prompt optimization from an existing draft.
2. Read minimal repo context using [references/project-scan-guide.md](references/project-scan-guide.md).
3. Optionally run the helper script for quick signal extraction:

```bash
python scripts/summarize_project_context.py --root <repo> --format json
```

4. Review prompt gaps with [references/prompt-review-rules.md](references/prompt-review-rules.md).
5. Produce output with [references/output-contract.md](references/output-contract.md).

## Command Shapes

Default JSON summary:

```bash
python scripts/summarize_project_context.py --root <repo>
```

Markdown summary for fast review:

```bash
python scripts/summarize_project_context.py --root <repo> --format markdown
```

Scoped summary:

```bash
python scripts/summarize_project_context.py --root <repo> --include apps/web --include packages/ui --max-depth 3
```

## Output Requirement

Always return exactly three sections:

- `Final Prompt`
- `Execution Advice`
- `Checklist`

## Examples

### Example 1: Generate a prompt from a vague task

```bash
python scripts/summarize_project_context.py --root . --format json
```

Use the JSON output to build a prompt that includes repository-specific constraints, file paths, and validation steps.

### Example 2: Optimize an existing draft prompt

1. Read the draft prompt.
2. Run `scripts/summarize_project_context.py` to gather repo signals.
3. Review gaps against `references/prompt-review-rules.md`.
4. Produce the optimized prompt with `Final Prompt`, `Execution Advice`, and `Checklist`.

## Guardrails

- Do not rewrite prompts generically; always anchor on repository signals.
- Do not over-scan large repos when a few files already establish constraints.
- Do not hide assumptions; list unknowns and proceed with safe defaults.
- Do not skip verification guidance in the final prompt package.

## References

- Read `references/project-scan-guide.md` for minimal repo context extraction.
- Read `references/prompt-review-rules.md` for common prompt gaps and fixes.
- Read `references/output-contract.md` for the required output structure.

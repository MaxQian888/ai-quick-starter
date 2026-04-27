# Triage Checklist

Open this file when the request is vague, mixes several concerns, or does not clearly identify the target feature yet.

## 1. Confirm the real target

- What exact folder, route, module, screen, API path, or command is being optimized?
- Is the user asking for a plan before coding, or do they actually want a fix now?
- Is the scope one feature, one subsystem, or a whole repository?
- Is the goal performance, maintainability, UX, test coverage, stability, or a combination?

## 2. Lock the right surface

- Find the entrypoint or main owning module.
- Find the state owner, service owner, and test owner.
- Find the docs, specs, or tickets that define intended behavior.
- Find the real quality gates that apply to this repository.

## 3. Classify the optimization question

| User question shape | Primary emphasis |
| --- | --- |
| "How should we optimize this feature?" | Full workflow: code study, validation, research, plan |
| "What is missing or incomplete here?" | Feature inventory plus gap and acceptance-criteria analysis |
| "Why is this flow slow or fragile?" | Performance, lifecycle, and error-handling audit |
| "Is this implementation still current?" | Best-practice drift and official-doc comparison |
| "What should we improve first?" | Prioritized backlog and quick wins |

## 4. Prefer another skill when needed

- Prefer `$build-project-fixer` when the core task is to reproduce and repair the behavior now.
- Prefer `$project-optimization-opportunity-auditor` when the user wants repository-wide prioritization.
- Prefer `$feature-gap-requirements-auditor` when the main task is docs-versus-code requirement matching.
- Prefer `$project-architecture-design-analyzer` when the target surface is still too vague to map directly.

## 5. Only then start the audit

- Restate the scope in one sentence.
- Keep the pass analysis-only.
- Gather local evidence before external research.
- Save implementation ideas for the final plan instead of the initial read.

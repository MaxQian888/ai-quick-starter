---
name: project-optimization-opportunity-auditor
description: |
  Use whenever you need to analyze repository architecture, docs, specs, and plans to produce a prioritized optimization backlog with evidence. Make sure to use this skill whenever the user asks "what should we improve first", "optimization opportunities", "performance audit", "tech debt", "bottlenecks", "refactor priorities", "code health", or "where to invest engineering effort" — even for greenfield projects that need early structure decisions. Also trigger when reviewing a codebase before a roadmap planning session, preparing an engineering strategy doc, or deciding between rewrite vs refactor. Covers code quality, build performance, test coverage, documentation gaps, and architectural drift.
---

# Project Optimization Opportunity Auditor

## Overview

Build an evidence-backed optimization backlog from repository structure, planning docs, and command signals.

This skill is for **what should we improve first** decisions, not direct code repair.

## Adaptive Detection

Before auditing, detect project signals:

1. **Codebase maturity**: Check commit history, test coverage, and documentation depth.
2. **Build and CI**: Look for slow builds, flaky tests, or missing quality gates in CI configs.
3. **Architecture patterns**: Note monolith vs microservice, layered vs feature-based, or tight coupling.
4. **Tech debt indicators**: Search for TODOs, FIXMEs, deprecated dependencies, or outdated frameworks.
5. **Team constraints**: Consider team size, release frequency, and business priorities.

Use these signals to weight opportunities by feasibility and impact.

## Workflow

1. Confirm audit scope: whole repo or a narrowed target.
2. Run the helper script first:

```bash
python scripts/build_optimization_opportunity_report.py --root <repo>
```

3. If needed, narrow the scan:

```bash
python scripts/build_optimization_opportunity_report.py --root <repo> --target <path> --focus <keyword>
```

4. Read JSON output before Markdown.
5. Validate top backlog scores and evidence paths.
6. Route follow-up execution to linked skills.

## Useful Command Shapes

Full scan:

```bash
python scripts/build_optimization_opportunity_report.py --root <repo>
```

Targeted scan with explicit docs:

```bash
python scripts/build_optimization_opportunity_report.py --root <repo> --target src/auth --doc docs/specs/auth.md --focus login --top 5
```

Constrained scan with include and exclude filters:

```bash
python scripts/build_optimization_opportunity_report.py --root <repo> --include apps/web --exclude vendor --max-files 50
```

## Output Contract

The report must clearly separate:

- observed repository evidence,
- inferred optimization recommendations,
- blind spots and limits.

JSON keys to rely on:

- `repository_snapshot`
- `surface_records`
- `discovered_docs`
- `opportunities`
- `top_backlog`
- `category_summary`
- `linked_skills`
- `blind_spots`
- `limits`

## Linked Skill Routing

Use linked skills after backlog generation:

- `$project-architecture-design-analyzer` for architecture seam deep-dive.
- `$feature-gap-requirements-auditor` when docs/specs need docs-vs-code reconciliation.
- `$build-project-fixer` when command-surface verification or repair is needed.

## Examples

### Example 1: Full repository audit

```bash
python scripts/build_optimization_opportunity_report.py --root .
```

### Example 2: Targeted scan on authentication subsystem

```bash
python scripts/build_optimization_opportunity_report.py --root . --target src/auth --doc docs/specs/auth.md --focus login --top 5
```

## References

- [references/analysis-playbook.md](references/analysis-playbook.md)
- [references/output-schema.md](references/output-schema.md)
- [references/scoring-rubric.md](references/scoring-rubric.md)
- [references/linked-skills.md](references/linked-skills.md)

## Guardrails

- Do not claim runtime truth from static analysis only.
- Do not auto-apply code changes from this skill output.
- Do not hide limits: always report blind spots and truncation.
- Do not over-scan when a target path is already provided.

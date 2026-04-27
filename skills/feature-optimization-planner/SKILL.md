---
name: feature-optimization-planner
description: Use whenever auditing a specific folder, feature, or module for optimization opportunities, creating code quality improvement plans, analyzing technical debt, or planning refactoring work with evidence-backed recommendations. Make sure to use this skill for performance audits, maintainability reviews, type safety improvements, testing gap analysis, security reviews, or architecture quality assessments on a bounded subsystem. Also triggers for optimization roadmaps, quick-win identification, or any request involving understanding what to improve before making code changes.
---

# Feature Optimization Planner

Audit a narrow implementation surface first. Build an evidence-backed optimization plan that stays scoped to the requested folder or feature and does not modify code during the audit pass.

## Adaptive Detection

Before auditing, scan the workspace to understand the project context:

1. Detect tech stack and toolchain:
   - Look for `package.json` (Node.js), `Cargo.toml` (Rust), `pyproject.toml` (Python), `go.mod` (Go).
   - Check for build tools (Vite, Webpack, Next.js, Cargo, Poetry).
   - Identify test runners (Vitest, Jest, pytest, cargo test).
2. Detect existing quality tools:
   - Look for linter configs (ESLint, Clippy, Ruff, golangci-lint).
   - Check for type checkers (TypeScript, mypy, Rust compiler).
   - Identify formatter configs (Prettier, rustfmt, black).
3. Detect target surface:
   - Identify the exact folder, file, or feature from the user's request.
   - Look for corresponding test files and documentation.
4. Detect project conventions:
   - Check `AGENTS.md` or `CLAUDE.md` for project-specific rules.
   - Look for existing optimization plans or technical debt documents.

## Use This Skill If

- The request is about one feature, folder, route, or bounded subsystem.
- The user wants an optimization plan before implementation.
- The audit should cover maintainability, performance, type safety, testing, security, or architecture quality.
- The answer should stay evidence-backed and scoped rather than turning into a whole-repo rewrite.

## Prefer Another Skill If

- Use `$project-optimization-opportunity-auditor` for a whole-repo backlog.
- Use `$feature-gap-requirements-auditor` when the main task is docs-versus-code completeness.
- Use `$project-architecture-design-analyzer` when ownership seams or repository boundaries are still unclear.
- Use `$build-project-fixer` when the main task is to reproduce and repair behavior now, not just plan the work.

## Start Here

1. Restate the repository root, exact target, and optimization goal in one sentence.
2. Keep the pass analysis-only. Do not edit code while using this skill.
3. Read [references/triage-checklist.md](references/triage-checklist.md) when the prompt is vague or mixes several concerns.
4. Read [references/research-playbook.md](references/research-playbook.md) before broad file reads or exact-string scans.
5. Read [references/plan-template.md](references/plan-template.md) before drafting the final report.
6. Read [references/evidence-framing.md](references/evidence-framing.md) when the output needs clear wording for observed facts, verified results, inferred risks, and open questions.

## Quick Reference

| Situation | Move |
| --- | --- |
| Prompt is vague or mixed | Read [references/triage-checklist.md](references/triage-checklist.md) first |
| Owning files are unclear | Use semantic search before exact `rg` |
| Stack behavior may have drifted | Query official docs first, then broader web research |
| User wants repo-wide prioritization | Route to `$project-optimization-opportunity-auditor` |
| User wants fixes now | Route to `$build-project-fixer` after the planning pass or instead of it |
| Final wording needs confidence labels | Use [references/evidence-framing.md](references/evidence-framing.md) |

## Workflow

1. Confirm the repository root, exact target folder, and the user's real optimization goal.
2. Inventory the target surface before drawing conclusions:
   - list files and subdirectories,
   - group source, tests, config, and docs,
   - note large files, thin test coverage, and likely entrypoints.
3. Use semantic code search before exact grep:
   - prefer augment context engine when the owning files, seams, or dependencies are not obvious,
   - use exact `rg` only after the surface is narrowed.
4. Read the target in dependency order:
   - entrypoints,
   - state or stores,
   - services or hooks,
   - utilities and shared types,
   - tests and fixtures,
   - local docs or specs.
5. Run the issue checklist across structure, readability, error handling, performance, type safety, security, and testing.
6. If stack-specific guidance matters, query current official docs first. Use broader web search only after official docs or standards are checked.
7. Produce a prioritized optimization plan with evidence, expected benefit, effort, action order, and quick wins.
8. Stop after the plan. Execute fixes only in a separate implementation pass.

## What To Deliver

The final deliverable should include:

- a short executive summary,
- issue counts by priority,
- itemized optimization entries with concrete evidence,
- recommended execution order,
- estimated total effort,
- quick wins,
- blind spots or open questions that could change the plan.

Use [references/plan-template.md](references/plan-template.md) as the default report shape.
Use [references/evidence-framing.md](references/evidence-framing.md) when wording the confidence level of findings.

## Examples

### Example 1: React Component Audit

**Input:** "Audit the dashboard components for performance issues."

**Output:**
- Inventories `src/dashboard/` files.
- Identifies unnecessary re-renders, missing memoization, and large bundle imports.
- Prioritizes quick wins (memoization) before structural changes.

### Example 2: API Route Review

**Input:** "Review the payment API routes for security and error handling."

**Output:**
- Maps entrypoints to service layer.
- Identifies missing input validation, inconsistent error responses, and lack of rate limiting.
- Provides evidence-backed recommendations with effort estimates.

## Linked Skill Routing

- Read [references/linked-skills.md](references/linked-skills.md) when the audit identifies a narrower follow-up task.
- Use `$project-optimization-opportunity-auditor` when the user wants a whole-repo backlog instead of one folder or feature.
- Use `$feature-gap-requirements-auditor` when the main question is docs-vs-code completeness, not broad code quality.
- Use `$project-architecture-design-analyzer` when the main risk is ownership, module boundaries, or repository structure.
- Use `$build-project-fixer` when validation commands, failing checks, or runtime verification need their own discovery pass.
- Use `$component-unit-test-completer` only after the audit establishes a concrete missing-test backlog worth implementing.

## Common Mistakes

- Jumping to fixes before inventorying the current feature surface.
- Assuming generic commands like `pnpm lint` or `pnpm test` without reading the repository's real command surface.
- Turning one folder audit into a repo-wide architectural rewrite without evidence.
- Treating static code reading as runtime proof.
- Treating blog posts as stronger evidence than official docs when stack behavior is the issue.

## Guardrails

- Do not modify code during the audit pass.
- Do not report issues without path-level evidence.
- Do not widen a folder audit into a repo-wide rewrite unless the user asks.
- Do not present static guesses as runtime truth.
- Do not rely on stale memory for framework guidance when official current docs are easy to verify.
- Do not hide uncertainty. If business intent, runtime behavior, or external dependencies are unclear, keep that uncertainty visible in the plan.

## References

- Read [references/example-prompts.md](references/example-prompts.md) for realistic user prompts that should trigger this skill or route to a different one.
- Read [references/triage-checklist.md](references/triage-checklist.md) when the request is vague and you need to lock the right scope quickly.
- Read [references/research-playbook.md](references/research-playbook.md) for tool mapping, discovery order, exact-search patterns, and external research rules.
- Read [references/issue-catalog.md](references/issue-catalog.md) for the full audit checklist and priority heuristics.
- Read [references/plan-template.md](references/plan-template.md) when shaping the final optimization report.
- Read [references/evidence-framing.md](references/evidence-framing.md) when translating findings into evidence-backed language.
- Read [references/linked-skills.md](references/linked-skills.md) when the next step should hand off to a narrower or execution-focused skill.

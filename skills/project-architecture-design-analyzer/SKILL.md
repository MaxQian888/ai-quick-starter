---
name: project-architecture-design-analyzer
description: |
  Use this skill whenever you need to understand a codebase's architecture, design patterns, or structural seams — whether you say "analyze this repo", "how is this project organized", "what's the architecture", "codebase overview", "project structure", "tech stack", or simply point at a repository before refactoring or documenting. Make sure to use this skill first on any unfamiliar repository to avoid blind manual reading. Also trigger when choosing a follow-up skill for deeper work (indexing, tracing, context initialization, or build verification). Covers monorepos, microservices, single-page apps, backend services, and mixed-language repositories.
---

# Project Architecture Design Analyzer

Get the shape of a repository first, then decide how to go deeper. The report you generate is a snapshot grounded in what the files actually show — not a claim about what happens at runtime.

## Adaptive Detection

Before analyzing, detect repository signals:

1. **Manifest files**: Check for `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `pom.xml`, or `build.gradle`.
2. **Workspace tools**: Look for `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, or `Cargo.toml` workspaces.
3. **Framework indicators**: Detect Next.js, React, Vue, Tauri, Django, Flask, Spring Boot, or Express from dependencies and file patterns.
4. **CI/CD**: Check `.github/workflows/`, `.gitlab-ci.yml`, `azure-pipelines.yml`, or Jenkinsfiles.
5. **Documentation**: Note presence of `README.md`, `CLAUDE.md`, `docs/`, `ARCHITECTURE.md`, or `CONTRIBUTING.md`.

Use these signals to focus the analysis and choose the right follow-up skills.

## Workflow

1. Confirm the repository root and what the user actually wants to know.
2. Before opening files by hand, run the helper script:

   ```bash
   python scripts/build_project_architecture_report.py --root <repo>
   ```

3. If the user already cares about a specific subsystem, feature, or concern, add `--focus`:

   ```bash
   python scripts/build_project_architecture_report.py --root <repo> --focus <keyword>
   ```

4. For large or noisy repositories, narrow the scope with `--include` or `--exclude` instead of trying to read everything manually:

   ```bash
   python scripts/build_project_architecture_report.py --root <repo> --include apps/web --exclude vendor
   ```

5. Read the JSON output first, then the Markdown report.
6. Use the `summary`, `architecture`, `linked_skills`, and `suggested_next_reads` fields to decide what to inspect next.
7. When you answer, keep raw file observations separate from conclusions you are drawing from them.

## How to Read the Report

Start with the high-level fields, then drill in:

- `summary.docs`, `summary.manifests`, and `summary.commands`: the quickest clues about what the project is supposed to do and how to run it.
- `architecture.entry_candidates`: likely bootstrap files or top-level seams worth opening first.
- `architecture.top_directories`: the biggest ownership buckets in the repo.
- `architecture.boundaries`: cross-directory handoffs observed from static imports.
- `architecture.design_patterns`: coarse patterns like layered services, UI/service splits, or documentation-driven context.
- `architecture.drift_risks`: signals that deserve caution — missing docs, thin tests, mixed runtimes, or tight coupling.
- `linked_skills`: recommended follow-up skills and when each makes sense.
- `suggested_next_reads`: the smallest file set that is actually worth opening next.

## Choosing a Linked Skill

- Reach for `$codebase-indexing-assistant` when the architecture pass needs a broader repo map, more file-level coverage, or a better reading order.
- Reach for `$feature-call-chain-mapper` when the next question is about feature flow, request paths, or handler-to-service tracing.
- Reach for `$project-ai-context-initializer` when the report says root context docs are thin or missing and the team needs durable navigation docs.
- Reach for `$build-project-fixer` when commands or manifests need runtime verification before you trust any design assumptions.
- Reach for `$project-skill-builder` when this repository will be revisited enough that the analysis should become a reusable, repo-specific skill.

If more than one follow-up skill looks plausible, read [references/linked-skills.md](references/linked-skills.md) before deciding.

## Guardrails

- Static findings are not runtime proof. Don't present them as if they are.
- Don't say a command works unless you have verified it separately.
- Don't fall back to repository-wide manual reading when `--focus`, `--include`, or `--exclude` would be a better next step.
- Be upfront about uncertainty. Report design drift and blind spots plainly.
- Linked-skill recommendations are options backed by evidence, not mandatory jumps.

## Examples

### Example 1: Quick architecture snapshot

```bash
python scripts/build_project_architecture_report.py --root .
```

### Example 2: Focused analysis on a subsystem

```bash
python scripts/build_project_architecture_report.py --root . --focus auth --include apps/web
```

## References

- [references/analysis-playbook.md](references/analysis-playbook.md) — command shapes, narrowing rules, and how to frame your answer.
- [references/output-schema.md](references/output-schema.md) — the JSON and Markdown output contract.
- [references/linked-skills.md](references/linked-skills.md) — how to choose the right follow-up skill.

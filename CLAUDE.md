# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

`ai-quick-starter` is a public, bilingual (Chinese/English) Claude Code skills collection. The repository root doubles as a Claude plugin, and individual skills are exposed through `.claude-plugin/marketplace.json` under the marketplace name `astroair-skills`.

This is not a monolithic application. It is a curated set of independent, reusable skills, each focused on a single task (e.g., `build-project-fixer`, `screenshot`, `code-simplifier`).

## High-Level Architecture

### Skill-Centric Structure

Every skill is self-contained under `skills/<skill-name>/`. There is no root-level build system, package manager, or shared dependency tree. Treat each skill as an independent module.

Standard skill layout:

```
skills/<skill-name>/
  SKILL.md           # Behavior, triggers, and workflow documentation
  agents/            # Agent contracts (e.g., openai.yaml)
  references/        # Stable guidance and documentation
  scripts/           # Repeatable helper scripts (usually Python)
  tests/             # unittest-based script verification
  evals/             # Evaluation definitions (e.g., evals.json)
  assets/            # Example inputs or fixtures
  artifacts/         # Generated example outputs
```

Skills may omit directories they do not need. Not every skill has scripts or tests.

### Plugin and Marketplace Layer

- `.claude-plugin/plugin.json` — Root plugin metadata.
- `.claude-plugin/marketplace.json` — Marketplace catalog. Lists the bundle plugin `ai-quick-starter` and is the source of truth for marketplace exposure.
- `plugins/` — Generated artifact directory (gitignored). The README documents regenerating it with `uv run --python 3.11 scripts/build_marketplace_plugins.py --repo-root .`, but this script does not currently exist in the repository.

### Codex Configuration

`codex/config.toml` contains Codex-specific settings including model provider configuration, MCP server definitions, and feature flags. Modify this only when adding or updating Codex-level integrations.

## Common Commands

### Running Skill Tests

There is no root test runner. Tests live inside individual skills and use Python's built-in `unittest`.

Run a single skill's tests:

```bash
cd skills/<skill-name> && python -m unittest discover -s tests -v
```

Or run a specific test file directly:

```bash
python skills/<skill-name>/tests/test_<module>.py
```

**Note on test portability:** Some older test files hardcode absolute paths such as `D:\Project\skills-test`. Newer tests use `importlib.util` to load scripts relative to `__file__`. When adding tests, prefer the relative `importlib.util` pattern.

### Adding or Modifying a Skill

1. Create or edit the skill directory under `skills/<skill-name>/`.
2. Add or update `SKILL.md` with trigger conditions and workflow.
3. Add helper scripts under `scripts/` when the workflow is automatable.
4. Add `tests/` when scripts need behavioral verification.
5. Update `README.md` if the skill is user-facing and should appear in the public catalog.
6. Update `CHANGELOG.md` for notable additions or changes.

There is no lint, typecheck, or build step at the repository root. Validate changes by reading Markdown for formatting drift and running the relevant skill's tests.

### Regenerating Marketplace Metadata

The README documents this command, but the script is not currently present in the repository:

```bash
uv run --python 3.11 scripts/build_marketplace_plugins.py --repo-root .
```

If the script exists in the future, this generates the `plugins/` wrappers and refreshes marketplace metadata without duplicating skill content.

## Conventions

- **Bilingual docs:** Public-facing documentation (`README.md`, `SKILL.md`, `CHANGELOG.md`) should be bilingual (Chinese and English) when possible.
- **No secrets:** Do not commit API keys, tokens, cookies, or local-only settings.
- **Generated artifacts:** Keep `plugins/`, cache directories, and local tooling output out of git.
- **Focused changes:** Prefer small, reviewable changes scoped to a single skill. Avoid repo-wide refactors unless discussed.

## Entry Points for Common Tasks

| Task | Where to look |
|------|---------------|
| Understand a skill's purpose | `skills/<skill-name>/SKILL.md` |
| Run a skill's helper script | `skills/<skill-name>/scripts/` |
| Verify a skill's behavior | `skills/<skill-name>/tests/` |
| See agent contract | `skills/<skill-name>/agents/openai.yaml` |
| Contributing rules | `CONTRIBUTING.md` |
| Security reporting | `SECURITY.md` |
| Plugin metadata | `.claude-plugin/marketplace.json` |

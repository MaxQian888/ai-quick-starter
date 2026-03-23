# CLAUDE.md

Breadcrumbs: [Repository Root](../CLAUDE.md) / agents-team-builder / CLAUDE.md

## Purpose

`agents-team-builder` is a workflow-aware generator that turns a project brief into structured Codex subagent planning artifacts.

It is one of the strongest onboarding examples in this repository because it combines:

- a clear `SKILL.md`,
- UI metadata,
- focused references,
- a non-trivial Python generator,
- tests,
- example assets,
- and generated example artifacts.

## Module Map

```mermaid
flowchart TD
  root["agents-team-builder/"] --> skill["SKILL.md<br/>Trigger, workflow, guardrails"]
  root --> meta["agents/openai.yaml<br/>Display metadata"]
  root --> refs["references/<*.md><br/>Schema and workflow rules"]
  root --> script["scripts/build_agents_team.py<br/>Main generator CLI"]
  root --> tests["tests/test_build_agents_team.py<br/>Behavior contract"]
  root --> assets["assets/examples/<*.md|*.json><br/>Stable sample inputs and outputs"]
  root --> artifacts["artifacts/<generated outputs><br/>Read only when examples are needed"]
```

## Entry Points

Read files in this order:

1. `SKILL.md`
2. `references/workflow-profiles.md`
3. `references/team-schema.md`
4. `scripts/build_agents_team.py`
5. `tests/test_build_agents_team.py`
6. `assets/examples/`

## Main Interface

The script-backed CLI lives in `scripts/build_agents_team.py`.

Primary inputs:

- `--input`
- `--output-dir`
- `--project-name`

Optional context inputs:

- `--config-file`
- `--agents-dir`
- `--agents-md`

Explicit output paths:

- `--json-out`
- `--markdown-out`

Workflow shaping:

- `--workflow-profile`
- supported profiles include `auto`, `generic`, `superpowers-plan`, `openspec-core`, and `openspec-expanded`

Install lifecycle:

- `--install`
- `--uninstall`
- `--manifest`
- `--codex-home`

## Output Contract

The generator emits structured artifacts rather than loose prose:

- one Markdown report
- one JSON document
- one `.toml` draft per generated agent role
- optional install records when install mode is used

The JSON and Markdown schema is described in `references/team-schema.md`.

## Behavioral Notes

- The generator is heuristic-driven, not a full dependency analyzer.
- Workflow awareness is part of the contract, especially for `superpowers` and OpenSpec-style flows.
- The install path is optional and should be treated as a managed lifecycle with manifests, not ad hoc file copying.
- `artifacts/` is example evidence, not the canonical implementation surface.

## Dependencies And Test Shape

- Implementation uses Python standard library only.
- Tests focus on deterministic behavior:
  - task extraction
  - parallel grouping
  - TOML draft rendering
  - workflow-profile detection
  - install and uninstall behavior

## When To Read This Module

Read this module when you need examples of:

- script-backed skill authoring
- workflow-aware structured outputs
- machine-readable artifact contracts
- install and uninstall manifest behavior
- mixing `SKILL.md`, references, assets, and tests in one skill package

## Related Guides

- Design history: [../docs/superpowers/CLAUDE.md](../docs/superpowers/CLAUDE.md)
- Repo indexing utility: [../codebase-indexing-assistant/CLAUDE.md](../codebase-indexing-assistant/CLAUDE.md)
- Guarded audit utility: [../guarded-component-i18n-fix/CLAUDE.md](../guarded-component-i18n-fix/CLAUDE.md)

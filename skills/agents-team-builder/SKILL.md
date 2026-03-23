---
name: agents-team-builder
description: Generate Codex subagent team plans, prompt templates, and `.toml` drafts from a complex project brief or task list. Use when Codex needs to split work into serial and parallel tracks, map tasks to `default` or `worker` or `explorer` or custom roles, output reviewable agent configs, or produce structured Markdown and JSON artifacts instead of loose multi-agent advice.
---

# Agents Team Builder

## Overview

Turn a broad project brief into a small, reviewable Codex subagent team. Default to stable artifacts: one Markdown team plan, one matching JSON document, and one `.toml` draft per agent.

This skill is workflow-aware. It can keep the generic path, or detect common process families such as `superpowers` plan execution and OpenSpec `opsx` workflows.

## Start Here

1. Confirm the main request source:
   - a natural-language brief,
   - a task list,
   - or a brief plus existing `config.toml`, `~/.codex/agents/*.toml`, or `AGENTS.md`.
2. Run the generator before freehand planning:

```bash
python scripts/build_agents_team.py --input <brief.md> --output-dir <out-dir>
```

If the brief already names a workflow, let the script detect it automatically. If you need to force a profile, use:

```bash
python scripts/build_agents_team.py --input <brief.md> --workflow-profile superpowers-plan
```

3. Read the generated JSON first. Use the Markdown report for rendering and review.
4. Deepen only on the sections that need adjustment: task decomposition, parallel groups, prompts, or `.toml` drafts.

## Workflow Rules

### 1. Decompose Before Naming Agents

Do not start from role names. Start from tasks, dependencies, and merge points. Read [references/decomposition-rules.md](references/decomposition-rules.md) when the parallel boundary is unclear.

### 2. Keep Parallelism Honest

Only parallelize tasks whose next action is not blocked by another task's output. Separate read-heavy exploration from write-heavy implementation whenever possible.

### 3. Prefer Small Teams

Default to the built-in roles first:
- `default` for synthesis, integration, and fallback support
- `worker` for execution and fixes
- `explorer` for read-heavy discovery

Add custom roles only when they materially reduce ambiguity or merge risk.

### 4. Emit Structured Artifacts

The generator must produce:
- one Markdown team plan,
- one JSON truth-source,
- and `.toml` drafts in a local output directory.

Read [references/team-schema.md](references/team-schema.md) when you need the exact JSON and Markdown contract.

### 5. Treat TOML As Drafts Until Install Time

Do not install generated `.toml` files into `~/.codex/agents/` unless the user explicitly asks for `--install`. When install mode is used, the tool must write a manifest and only manage files that manifest owns.

### 6. Respect Workflow Boundaries

If the request matches a known workflow:
- use the workflow profile to shape extra roles and guardrails,
- keep design and planning gates serial,
- and only parallelize the implementation or exploration phases that the workflow actually allows.

Read [references/workflow-profiles.md](references/workflow-profiles.md) first when the request names `superpowers`, `writing-plans`, `subagent-driven-development`, `verification-before-completion`, `OpenSpec`, or `opsx:*`.

## Command Shapes

Basic usage:

```bash
python scripts/build_agents_team.py --input <brief.md> --output-dir <out-dir>
```

With explicit project name:

```bash
python scripts/build_agents_team.py --input <brief.md> --project-name "ecommerce-rebuild" --output-dir <out-dir>
```

With existing config context:

```bash
python scripts/build_agents_team.py \
  --input <brief.md> \
  --config-file <config.toml> \
  --agents-dir <agents-dir> \
  --agents-md <AGENTS.md> \
  --output-dir <out-dir>
```

Stable output paths:

```bash
python scripts/build_agents_team.py \
  --input <brief.md> \
  --json-out <team>.json \
  --markdown-out <team>.md
```

Force a specific workflow profile:

```bash
python scripts/build_agents_team.py \
  --input <brief.md> \
  --workflow-profile openspec-expanded \
  --output-dir <out-dir>
```

Install generated agents into Codex:

```bash
python scripts/build_agents_team.py \
  --input <brief.md> \
  --output-dir <out-dir> \
  --install
```

Uninstall a previously installed team:

```bash
python scripts/build_agents_team.py \
  --uninstall \
  --project-name "ecommerce-rebuild"
```

## What To Read In The Output

- `task_graph`: the normalized work items and their dependency edges
- `workflow_profile`: the active process family used to shape the team
- `workflow_detection`: why that profile was selected
- `workflow_steps`: workflow stages and their parallelism rules
- `workflow_integrations`: skill or slash-command integrations to preserve
- `parallel_groups`: the safe same-phase batches
- `agents`: the recommended built-in and custom agent roster
- `prompts`: reusable spawn or assignment prompts
- `toml_files`: the reviewable config drafts
- `install_manifest`: the install record used for precise uninstall
- `installed_files`: the files copied into Codex during install mode
- `install_actions`: created vs overwritten actions for each installed file
- `execution_plan`: the ordered handoff sequence
- `risks` and `open_questions`: the limits that must not be hand-waved away

## Guardrails

- Do not create parallel worker agents with overlapping write scopes unless the merge point is explicit.
- Do not recommend a custom role when `default`, `worker`, or `explorer` already cover the need.
- Do not claim Codex will automatically pick the generated roles. These are planning artifacts, not runtime guarantees.
- Do not turn the output into freeform prose that loses the JSON structure.
- Do not delete or overwrite files in `~/.codex/agents/` without recording them in the install manifest first.
- Do not uninstall files that were not installed by a recorded manifest.
- Do not parallelize OpenSpec planning artifacts and active implementation in the same uncontrolled batch.
- Do not skip `verification-before-completion` or equivalent verify/archive gates when the workflow requires them.

## Reference Files

- Read [references/decomposition-rules.md](references/decomposition-rules.md) for dependency and parallelism heuristics.
- Read [references/team-schema.md](references/team-schema.md) for the Markdown and JSON contract.
- Read [references/workflow-profiles.md](references/workflow-profiles.md) for profile selection and auto-detection rules.
- Read [references/superpowers-integration.md](references/superpowers-integration.md) for the `brainstorming -> writing-plans -> subagent-driven-development/executing-plans -> verification-before-completion` chain.
- Read [references/openspec-integration.md](references/openspec-integration.md) for `opsx` core and expanded workflow mapping.
- Read [references/codex-subagents-notes.md](references/codex-subagents-notes.md) for Codex-specific caveats around config layout, built-in roles, and draft installation.
- Read [references/prompt-patterns.md](references/prompt-patterns.md) for prompt and developer-instruction templates.

## Example Assets

- Use [assets/examples/ecommerce-input.md](assets/examples/ecommerce-input.md) as a sample brief.
- Use [assets/examples/ecommerce-team.json](assets/examples/ecommerce-team.json) as a sample machine-readable output.
- Use [assets/examples/superpowers-input.md](assets/examples/superpowers-input.md) for a workflow-aware superpowers example.
- Use [assets/examples/openspec-input.md](assets/examples/openspec-input.md) for a workflow-aware OpenSpec example.

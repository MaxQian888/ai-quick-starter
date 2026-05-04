---
name: agents-team-builder
description: >
  Use this skill whenever you need to plan, design, or generate a multi-agent team from a project brief, task list, or existing plan — for either Codex subagents (.toml in ~/.codex/agents/) or Claude Code subagents and agent teams (.md with YAML frontmatter in ~/.claude/agents/).
  Make sure to use it when the user wants to break down work into parallel tasks, assign roles to subagents, create structured team plans, generate Claude Code subagent definition files, or produce a paste-in spawn brief for an experimental Claude Code agent team (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS).
  Also use it for keywords like "agent team", "subagent", "Codex agents", ".codex/agents", "Claude Code agents", ".claude/agents", "agent-teams", "teammates", "AgentTeam", or "split work across agents", even when the user does not explicitly ask for a planner.
  Covers workflow-aware decomposition for superpowers plans, OpenSpec opsx flows, and generic projects, with support for task graphs, parallel groups, prompt templates, installable .toml drafts, and installable Claude Code subagent .md files.
---

# Agents Team Builder

## Adaptive Detection

Before generating a team plan, scan for:
- The request source (natural-language brief, task list, or existing `config.toml` / `AGENTS.md`)
- The intended platform: Codex (`~/.codex/agents/*.toml`) or Claude Code (`~/.claude/agents/*.md` plus an optional agent-team brief). When in doubt, ask whether to target `codex`, `claude-code`, or `both`.
- Workflow keywords (`superpowers`, `OpenSpec`, `opsx`, `writing-plans`, `verification-before-completion`)
- Existing agent configs in `~/.codex/agents/`, `~/.claude/agents/`, `.claude/agents/`, or local `agents/` directories
- Project type (web app, library, infrastructure, documentation) to shape role selection
- Team size constraints and merge-point requirements

## Overview

Turn a broad project brief into a small, reviewable agent team. Default to stable artifacts: one Markdown team plan, one matching JSON document, and one `.toml` (Codex) or `.md` (Claude Code) draft per agent. When Claude Code is targeted, also produce a paste-in **team brief** that the user can hand to a Claude Code lead to spawn an experimental agent team — the team config itself (`~/.claude/teams/<team>/config.json`) is auto-managed runtime state and must not be pre-authored.

This skill is workflow-aware. It can keep the generic path, or detect common process families such as `superpowers` plan execution and OpenSpec `opsx` workflows. It is also platform-aware: the same task graph maps onto either Codex roles or Claude Code subagent definitions.

## Start Here

1. Confirm the main request source:
   - a natural-language brief,
   - a task list,
   - or a brief plus existing `config.toml`, `~/.codex/agents/*.toml`, `~/.claude/agents/*.md`, or `AGENTS.md`.
2. Choose a target platform with `--target`:
   - `codex` (default) — generate Codex `.toml` drafts in `~/.codex/agents/`.
   - `claude-code` — generate Claude Code subagent `.md` files in `~/.claude/agents/` plus a paste-in team brief.
   - `both` — generate both formats in parallel for cross-platform teams.
3. Run the generator before freehand planning:

```bash
python scripts/build_agents_team.py --input <brief.md> --output-dir <out-dir> --target claude-code
```

If the brief already names a workflow, let the script detect it automatically. If you need to force a profile, use:

```bash
python scripts/build_agents_team.py --input <brief.md> --workflow-profile superpowers-plan --target both
```

4. Read the generated JSON first. Use the Markdown report for rendering and review.
5. Deepen only on the sections that need adjustment: task decomposition, parallel groups, prompts, `.toml` drafts, Claude Code `.md` drafts, or the team brief.

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

Add custom roles only when they materially reduce ambiguity or merge risk. The Claude Code agent-teams docs recommend 3–5 teammates for most workflows; resist the urge to spawn more.

### 4. Emit Structured Artifacts

The generator must produce:
- one Markdown team plan,
- one JSON truth-source,
- `.toml` drafts (Codex target) and/or `.md` drafts (Claude Code target) in a local output directory,
- a team brief (`<project>-claude-team-brief.md`) when Claude Code is in the target set.

Read [references/team-schema.md](references/team-schema.md) when you need the exact JSON and Markdown contract.

### 5. Treat Drafts As Drafts Until Install Time

Do not install generated `.toml` files into `~/.codex/agents/` or `.md` files into `~/.claude/agents/` unless the user explicitly asks for `--install`. When install mode is used, the tool writes a per-target manifest under `<home>/agents/.agents-team-builder/manifests/` and only manages files that manifest owns.

### 6. Never Pre-Author Claude Code Team Configs

Claude Code's agent-team config (`~/.claude/teams/<team>/config.json`) holds runtime state — session IDs, tmux pane IDs, mailbox handles — and gets overwritten by Claude Code on the next state update. The skill therefore generates a **natural-language team brief** instead, which the user pastes into a Claude Code lead session that has `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set. The lead spawns teammates that reuse the generated subagent definitions.

### 7. Respect Workflow Boundaries

If the request matches a known workflow:
- use the workflow profile to shape extra roles and guardrails,
- keep design and planning gates serial,
- and only parallelize the implementation or exploration phases that the workflow actually allows.

Read [references/workflow-profiles.md](references/workflow-profiles.md) first when the request names `superpowers`, `writing-plans`, `subagent-driven-development`, `verification-before-completion`, `OpenSpec`, or `opsx:*`.

## Command Shapes

Basic usage (Codex default):

```bash
python scripts/build_agents_team.py --input <brief.md> --output-dir <out-dir>
```

Generate Claude Code subagent files plus a team brief:

```bash
python scripts/build_agents_team.py \
  --input <brief.md> \
  --output-dir <out-dir> \
  --target claude-code \
  --project-name "ecommerce-rebuild"
```

Generate both Codex and Claude Code artifacts for cross-platform teams:

```bash
python scripts/build_agents_team.py \
  --input <brief.md> \
  --output-dir <out-dir> \
  --target both
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

Install generated agents:

```bash
# Codex only (writes to ~/.codex/agents/)
python scripts/build_agents_team.py --input <brief.md> --output-dir <out-dir> --install

# Claude Code only (writes to ~/.claude/agents/)
python scripts/build_agents_team.py --input <brief.md> --output-dir <out-dir> --target claude-code --install

# Both (writes to both, separate manifests per target)
python scripts/build_agents_team.py --input <brief.md> --output-dir <out-dir> --target both --install
```

Override install destinations:

```bash
python scripts/build_agents_team.py \
  --input <brief.md> --output-dir <out-dir> --target both --install \
  --codex-home /path/to/.codex \
  --claude-home /path/to/.claude
```

Uninstall a previously installed team:

```bash
# Codex (default)
python scripts/build_agents_team.py --uninstall --project-name "ecommerce-rebuild"

# Claude Code
python scripts/build_agents_team.py --uninstall --project-name "ecommerce-rebuild" --target claude-code

# Both targets at once
python scripts/build_agents_team.py --uninstall --project-name "ecommerce-rebuild" --target both
```

## What To Read In The Output

- `target`: the active platform target (`codex`, `claude-code`, or `both`)
- `task_graph`: the normalized work items and their dependency edges
- `workflow_profile`: the active process family used to shape the team
- `workflow_detection`: why that profile was selected
- `workflow_steps`: workflow stages and their parallelism rules
- `workflow_integrations`: skill or slash-command integrations to preserve
- `parallel_groups`: the safe same-phase batches
- `agents`: the recommended built-in and custom agent roster
- `prompts`: reusable spawn or assignment prompts
- `toml_files`: Codex `.toml` config drafts (when target includes `codex`)
- `claude_code_files`: Claude Code subagent `.md` drafts (when target includes `claude-code`)
- `team_brief`: paste-in spawn prompt for a Claude Code agent team (when target includes `claude-code`)
- `install_manifest`: the install record(s) used for precise uninstall — a single dict for one target, a list of dicts for `--target both`
- `installed_files`: files copied into Codex/Claude Code during install mode (each entry tagged with `target`)
- `install_actions`: created vs overwritten actions for each installed file
- `execution_plan`: the ordered handoff sequence
- `risks` and `open_questions`: the limits that must not be hand-waved away

## Guardrails

- Do not create parallel worker agents with overlapping write scopes unless the merge point is explicit.
- Do not recommend a custom role when `default`, `worker`, or `explorer` already cover the need.
- Do not claim Codex or Claude Code will automatically pick the generated roles. These are planning artifacts, not runtime guarantees.
- Do not turn the output into freeform prose that loses the JSON structure.
- Do not delete or overwrite files in `~/.codex/agents/` or `~/.claude/agents/` without recording them in the corresponding install manifest first.
- Do not uninstall files that were not installed by a recorded manifest.
- Do not pre-author Claude Code team config files. `~/.claude/teams/<team>/config.json` is runtime state managed by Claude Code and gets overwritten on each state update.
- Do not parallelize OpenSpec planning artifacts and active implementation in the same uncontrolled batch.
- Do not skip `verification-before-completion` or equivalent verify/archive gates when the workflow requires them.
- When generating Claude Code subagent definitions, set `tools` conservatively for read-only roles (`Read, Grep, Glob, WebFetch, WebSearch`) and only loosen via `disallowedTools` rather than handing every subagent unrestricted Edit/Write/Bash.

## Reference Files

- Read [references/decomposition-rules.md](references/decomposition-rules.md) for dependency and parallelism heuristics.
- Read [references/team-schema.md](references/team-schema.md) for the Markdown and JSON contract.
- Read [references/workflow-profiles.md](references/workflow-profiles.md) for profile selection and auto-detection rules.
- Read [references/superpowers-integration.md](references/superpowers-integration.md) for the `brainstorming -> writing-plans -> subagent-driven-development/executing-plans -> verification-before-completion` chain.
- Read [references/openspec-integration.md](references/openspec-integration.md) for `opsx` core and expanded workflow mapping.
- Read [references/codex-subagents-notes.md](references/codex-subagents-notes.md) for Codex-specific caveats around config layout, built-in roles, and draft installation.
- Read [references/claude-code-subagents-notes.md](references/claude-code-subagents-notes.md) for Claude Code-specific frontmatter, scope, agent-team semantics, and tooling caveats.
- Read [references/prompt-patterns.md](references/prompt-patterns.md) for prompt and developer-instruction templates.

## Example Assets

- Use [assets/examples/ecommerce-input.md](assets/examples/ecommerce-input.md) as a sample brief.
- Use [assets/examples/ecommerce-team.json](assets/examples/ecommerce-team.json) as a sample machine-readable output.
- Use [assets/examples/superpowers-input.md](assets/examples/superpowers-input.md) for a workflow-aware superpowers example.
- Use [assets/examples/openspec-input.md](assets/examples/openspec-input.md) for a workflow-aware OpenSpec example.

## Examples

**Example 1: Plan a Codex subagent team for a project brief**
```
User: "I need to rebuild our ecommerce platform. Can you plan a Codex team for it?"
Agent: Run `python scripts/build_agents_team.py --input brief.md --output-dir ./team`, read the generated JSON for task_graph and parallel_groups, review the Markdown plan, and present the recommended agent roster with risks and open questions.
```

**Example 2: Generate Claude Code subagents and an agent-team brief**
```
User: "Make me a Claude Code agent team for this OpenSpec change."
Agent: Run `python scripts/build_agents_team.py --input brief.md --target claude-code --output-dir ./team`. Confirm CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 is set, walk the user through the generated <project>-claude-team-brief.md (which is the paste-in spawn prompt) and the per-role .md files in claude-agents/, and explain that the team config itself is auto-managed by Claude Code.
```

**Example 3: Cross-platform install for a workflow that uses both Codex and Claude Code**
```
User: "I run Codex for repo work and Claude Code for review. Can you set up a shared team for both?"
Agent: Run `python scripts/build_agents_team.py --input brief.md --target both --install`. Confirm the per-target manifests under ~/.codex/agents/.agents-team-builder/manifests/ and ~/.claude/agents/.agents-team-builder/manifests/, and remind the user that uninstall takes the same --target flag.
```

**Example 4: Generate OpenSpec-aware Claude Code team configuration**
```
User: "Plan agents for our OpenSpec opsx:auth-refactor workflow on Claude Code."
Agent: Run the generator with `--target claude-code` and either auto-detected workflow profile or `--workflow-profile openspec-expanded`. Ensure design and planning gates are serial, parallelize only implementation phases, include verification-before-completion gates in the execution plan, and present the team brief for the user to paste into Claude Code.
```

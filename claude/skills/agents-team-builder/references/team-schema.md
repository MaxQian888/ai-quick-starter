# Team Schema

Use this file when you need the exact structure of the generated artifacts.

## Markdown Sections

The Markdown report contains these sections in this order. `TOML Drafts`, `Claude Code Subagent Files`, and `Claude Code Team Brief` are conditional on the active `--target`.

1. `Request`
2. `Assumptions`
3. `Task Decomposition`
4. `Parallelization Plan`
5. `Agent Team`
6. `Prompt Templates`
7. `TOML Drafts` — present when `target` includes `codex`
8. `Claude Code Subagent Files` — present when `target` includes `claude-code`
9. `Claude Code Team Brief` — present when `target` includes `claude-code`
10. `Install Management` when install mode is used (per-target manifest entries)
11. `Execution Order`
12. `Risks And Guardrails`
13. `Open Questions`

## JSON Top-Level Fields

```json
{
  "request": {},
  "target": "codex | claude-code | both",
  "workflow_profile": "string",
  "workflow_detection": {},
  "workflow_steps": [],
  "workflow_integrations": [],
  "assumptions": [],
  "task_graph": [],
  "parallel_groups": [],
  "agents": [],
  "prompts": [],
  "toml_files": {},
  "claude_code_files": {},
  "team_brief": {},
  "install_manifest": {},
  "installed_files": [],
  "install_actions": [],
  "execution_plan": [],
  "risks": [],
  "open_questions": []
}
```

## `task_graph[]`

Each task object should include:

- `id`
- `title`
- `role`
- `phase`
- `description`
- `parallelizable`
- `reads_from`
- `writes_to`
- `depends_on`

## `parallel_groups[]`

Each parallel group should include:

- `group_id`
- `goal`
- `tasks`
- `max_concurrency`
- `why_parallelizable`
- `merge_point`

## `agents[]`

Each agent should include:

- `name`
- `role`
- `purpose`
- `model`
- `reasoning_effort`
- `sandbox_mode`
- `nickname_candidates`
- `developer_instructions`
- `owns_tasks`
- `reads_from`
- `writes_to`

## `toml_files{}`

Codex `.toml` drafts. Empty when `target == "claude-code"`. Each key is the file name, for example `worker.toml`.

Each value should carry:

- `path`
- `role`
- `content`

## `claude_code_files{}`

Claude Code subagent `.md` drafts. Empty when `target == "codex"`. Each key is the file name, for example `worker.md`.

Each value should carry:

- `path`
- `role`
- `name` — the Claude Code subagent name (lowercase + hyphens)
- `content`

## `team_brief{}`

Generated only when `target` includes `claude-code`. Carries the paste-in spawn prompt for an experimental Claude Code agent team.

- `path`
- `content`

## Install Management Fields

- `install_manifest`: object with `action`, `target`, and `path` for a single-target install. For `--target both`, this becomes a list of one such object per target so callers can route uninstall per target.
- `installed_files[]`: per-file install records with `destination_path`, `action`, `target`, and optional `backup_path`
- `install_actions[]`: quick summary of the file actions taken during install

The JSON is the truth source. The Markdown is the human review layer rendered from the same data.

## Workflow Fields

- `workflow_profile`: one of `generic`, `superpowers-plan`, `openspec-core`, `openspec-expanded`
- `workflow_detection`: detection mode, matched signals, and summary text
- `workflow_steps[]`: ordered process stages with notes about whether each stage is safe to parallelize
- `workflow_integrations[]`: named skills or slash commands that the generated team should preserve

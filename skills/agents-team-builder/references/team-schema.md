# Team Schema

Use this file when you need the exact structure of the generated artifacts.

## Markdown Sections

The Markdown report must contain these sections in this order:

1. `Request`
2. `Assumptions`
3. `Task Decomposition`
4. `Parallelization Plan`
5. `Agent Team`
6. `Prompt Templates`
7. `TOML Drafts`
8. `Install Management` when install mode is used
9. `Execution Order`
10. `Risks And Guardrails`
11. `Open Questions`

## JSON Top-Level Fields

```json
{
  "request": {},
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

Each key is the file name, for example `worker.toml`.

Each value should carry:

- `path`
- `role`
- `content`

## Install Management Fields

- `install_manifest`: object with `action` and `path`
- `installed_files[]`: per-file install records with `destination_path`, `action`, and optional `backup_path`
- `install_actions[]`: quick summary of the file actions taken during install

The JSON is the truth source. The Markdown is the human review layer rendered from the same data.

## Workflow Fields

- `workflow_profile`: one of `generic`, `superpowers-plan`, `openspec-core`, `openspec-expanded`
- `workflow_detection`: detection mode, matched signals, and summary text
- `workflow_steps[]`: ordered process stages with notes about whether each stage is safe to parallelize
- `workflow_integrations[]`: named skills or slash commands that the generated team should preserve

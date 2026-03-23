# Workflow Profiles

Use this file when the request names a process family and you need to know how `agents-team-builder` should react.

## Profiles

- `generic`: no workflow-specific shaping
- `superpowers-plan`: skill-driven design, planning, execution, and verification
- `openspec-core`: `opsx:propose -> opsx:apply -> opsx:archive`
- `openspec-expanded`: `opsx:explore/new/continue/ff/apply/verify/sync/archive`

## Auto-Detection Rules

### `superpowers-plan`

Select when the brief mentions one or more of:

- `superpowers:brainstorming`
- `superpowers:writing-plans`
- `superpowers:subagent-driven-development`
- `superpowers:executing-plans`
- `verification-before-completion`

### `openspec-core`

Select when the brief mentions OpenSpec or the core OPSX commands:

- `OpenSpec`
- `/opsx:propose`
- `/opsx:apply`
- `/opsx:archive`

### `openspec-expanded`

Select when the brief mentions any expanded OPSX command, such as:

- `/opsx:explore`
- `/opsx:new`
- `/opsx:continue`
- `/opsx:ff`
- `/opsx:verify`
- `/opsx:sync`
- `/opsx:bulk-archive`
- `/opsx:onboard`

Expanded signals take precedence over core signals.

## Manual Override

Use `--workflow-profile <name>` when the brief is ambiguous or when you need a deterministic profile for repeatable output.

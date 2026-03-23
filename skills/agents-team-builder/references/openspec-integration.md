# OpenSpec Integration

Use this file when the brief names OpenSpec or `opsx:*` commands.

## Core Workflow

The default OpenSpec path is:

1. `/opsx:propose`
2. `/opsx:apply`
3. `/opsx:archive`

### Core Mapping

- Planning artifacts should stay serial.
- `apply` can parallelize implementation tasks after artifacts are clear.
- `archive` is a closeout step and should not run in parallel with active implementation.

## Expanded Workflow

The expanded `opsx` path adds:

- `/opsx:explore`
- `/opsx:new`
- `/opsx:continue`
- `/opsx:ff`
- `/opsx:verify`
- `/opsx:sync`

### Expanded Mapping

- `explore` is the safest stage for parallel read-heavy work.
- `new`, `continue`, and `ff` are artifact-authoring stages; keep them controlled.
- `verify` and `sync` are closeout gates, not free-form implementation stages.
- `archive` happens only after verify and sync decisions are resolved.

## Recommended Extra Roles

### Core

- `proposal-writer`
- `spec-author`
- `design-author`
- `task-planner`
- `archiver`

### Expanded

- all core roles
- `workflow-explorer`
- `verifier`
- `sync-manager`

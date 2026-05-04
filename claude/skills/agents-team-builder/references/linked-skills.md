# Linked Skills

Use this file when the team plan identifies execution tasks that should be handed off to specialized skills.

## Execution Skills by Task Type

### `$build-project-fixer`
Use when the plan includes build, test, lint, or verification work.

### `$component-unit-test-completer`
Use when the plan includes unit test coverage gaps.

### `$e2e-test-completer`
Use when the plan includes end-to-end test updates or coverage gaps.

### `$github-actions-ci-builder`
Use when the plan includes CI workflow design or modernization.

### `$guarded-component-i18n-fix`
Use when the plan includes component-level i18n work.

### `$guarded-log-editor`
Use when the plan includes logging instrumentation or cleanup.

### `$commit-quality-fixer`
Use when the plan ends with a commit or push gate.

### `$development-task-orchestrator`
Use when the plan is ready to be turned into parallel execution waves, checkpoints, and main-thread duties.

## Analysis Skills by Task Type

### `$project-architecture-design-analyzer`
Use when the plan requires an architecture snapshot before implementation.

### `$feature-call-chain-mapper`
Use when the plan requires tracing a specific feature flow.

### `$feature-optimization-planner`
Use when the plan requires an optimization audit before refactoring.

## Routing Rules

- Map each task in the generated `task_graph` to the narrowest skill that covers it.
- Do not spawn parallel worker agents with overlapping write scopes unless the merge point is explicit.
- Keep design and planning gates serial; only parallelize implementation or exploration phases.
- Use `$build-project-fixer` as the verification gate before claiming any execution task is complete.

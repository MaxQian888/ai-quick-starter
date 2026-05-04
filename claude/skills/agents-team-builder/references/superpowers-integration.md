# Superpowers Integration

Use this file when the brief is about the local `superpowers` workflow rather than a generic multi-agent split.

## Canonical Chain

The common chain is:

1. `superpowers:brainstorming`
2. `superpowers:writing-plans`
3. `superpowers:subagent-driven-development` or `superpowers:executing-plans`
4. `superpowers:verification-before-completion`

## Parallelism Rules

- Keep brainstorming and writing-plans on the main thread or a tightly controlled planner role.
- Only parallelize the execution stage after the plan is approved.
- Preserve the review checkpoints from `subagent-driven-development`: implementation, spec review, then code-quality review.
- Always keep the final verification gate serial.

## Recommended Extra Roles

- `planner`
- `implementer`
- `spec-reviewer`
- `quality-reviewer`
- `final-reviewer`

These roles supplement the built-in `default`, `worker`, and `explorer` agents when the workflow demands stronger review structure.

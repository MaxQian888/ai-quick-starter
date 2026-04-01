---
name: spec-driven-develop
description: Use when Codex needs a pre-implementation workflow for a large rewrite, migration, architecture overhaul, or multi-phase feature program that will span multiple sessions and benefit from explicit analysis docs, tracked progress files, and a task-specific execution skill. Trigger for requests such as rewriting a project in another language, staging a large refactor, planning a long-running migration, setting up docs/progress/MASTER.md continuity, or asking for spec-driven development before coding.
---

# Spec-Driven Develop

Prepare large work before broad implementation starts. Confirm the target, analyze the real project surface, decompose the work into phases, materialize `docs/progress/` as the cross-session truth source, and hand off a focused execution skill only after the plan is stable.

## Workflow

1. If `docs/progress/MASTER.md` already exists, read it first and resume from the active phase instead of restarting the workflow.
2. Confirm the requested transformation, target state, constraints, and success criteria. If the request is still ambiguous, clarify the end state before planning.
3. Inspect the real project surface: entrypoints, manifests, tests, workflows, architecture seams, and migration risks. Keep observed facts separate from guesses.
4. Break the work into named phases with explicit tasks, dependencies, verification boundaries, and natural checkpoints.
5. Create or refresh `docs/progress/MASTER.md` plus one `phase-N-<name>.md` file per phase. Use `python scripts/bootstrap_progress_docs.py ...` when the phase list is already structured. Use `references/doc-templates.md` only when manual repair is needed.
6. Generate a focused execution skill only after the phase structure is stable. The child skill must always read `docs/progress/MASTER.md` first, update phase files after task completion, and preserve the phase verification boundaries.
7. Hand off only when the user has the analysis summary, phase plan, progress docs, and execution-skill location.

## Workflow Boundaries

- Stay in preparation mode. Do not start broad implementation work inside this skill unless the user explicitly switches from planning to execution.
- Use parallel analysis only when the project is large enough and the platform actually supports subagents. Otherwise work sequentially.
- Prefer project-specific evidence over generic migration playbooks.
- Keep progress files as the cross-session source of truth. Session-local task trackers are optional mirrors, not replacements.

## Guardrails

- Do not hide uncertain assumptions inside phase tasks. Mark them as open questions or risks.
- Do not create `docs/progress` files before the phase list is coherent.
- Do not stuff detailed templates or variant rules into `SKILL.md`; load the matching reference file instead.
- Do not generate a generic child skill that ignores the actual project, phase boundaries, or verification rules.
- Do not claim the preparation is complete until the progress files exist on disk and match the agreed phase breakdown.
- When all tracked tasks are complete, enter cleanup mode and ask whether to keep or remove temporary progress docs and the generated execution skill.

## References

- Read `references/workflow-phases.md` for the phase-by-phase protocol and resume rules.
- Read `references/progress-tracking.md` for the `docs/progress/` contract and when to use the bootstrap script.
- Read `references/sub-skill-generation.md` when creating the execution-focused child skill.
- Read `references/parallel-execution.md` before using subagents during analysis or later execution.
- Read `references/doc-templates.md` when you need manual Markdown templates or must repair drift in generated progress files.

## Helper Scripts

Bootstrap progress docs from a structured phase list:

```bash
python scripts/bootstrap_progress_docs.py --output-root <repo-root> --task-name "<task>" --task-summary "<summary>" --phase-file <phases.json>
```

Add `--overwrite` only when you intentionally want to replace an existing `docs/progress/` set.

Export existing progress docs to structured JSON:

```bash
python scripts/export_progress.py <repo-root>/docs/progress
```

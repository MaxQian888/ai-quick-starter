---
name: autonomous-loops
description: >
  Make sure to use this skill whenever the user wants to run autonomous agent loops,
  unattended iterations, batch tasks, or self-correcting workflows across Claude Code,
  Codex CLI, or OpenCode. Also trigger for sequential task automation, iterative
  improvement loops, parallel execution plans, session resumption, CI repair chains,
  or any request involving "run this repeatedly," "keep going until done," or
  "automate this workflow." Covers synonyms like "agent loop," "batch mode,"
  "unattended run," "iterative fix," "multi-step automation," "loop orchestration,"
  and "self-healing pipeline." Use it even when the user only mentions wanting to
  "automate" or "batch process" a set of tasks.
---

# Autonomous Loops

Design the loop first, then map it to the target CLI. Treat this skill as a compatibility-preserving home for loop orchestration guidance, not as a Claude-only cookbook.

## Adaptive Detection

Before generating loop commands, detect the execution context:

- Identify the target CLI: Claude Code, Codex CLI, or OpenCode.
- Determine the loop pattern from the task shape: sequential (one task), iterative (repeated passes), resume (continue prior work), or parallel-dag (dependency layers).
- Check if the current directory is a Git root; Codex often needs `--skip-git-repo-check`.
- Assess whether the task needs a notes file for cross-iteration state.

## Start Here

1. Classify the work with `references/pattern-selection.md`.
2. Map the chosen pattern to the target runner with `references/cli-adapters.md`.
3. Generate a starter command set with:

```bash
python scripts/render_loop_command.py --cli codex --pattern sequential --task "Implement the approved auth refactor"
```

4. Persist cross-iteration state in a small file such as `SHARED_TASK_NOTES.md` or `LOOP_STATE.md`.
5. Add explicit stop conditions before the first unattended run.

## Workflow

1. Choose the narrowest loop that fits the task.
2. Keep each iteration focused on one coherent step.
3. Use a filesystem bridge for context instead of stuffing every prior turn back into the prompt.
4. Add a dedicated cleanup or review pass rather than overloading the implementer prompt with negative rules.
5. Re-run the smallest relevant verification step before widening scope.
6. Record progress, blockers, and next-step hints at the end of each pass.

## Pattern Map

| Pattern | Use For | Notes |
| --- | --- | --- |
| `sequential` | One feature, one bugfix, or a short repair chain | Fresh context every pass, simplest automation surface |
| `iterative-pr` | Multi-iteration backlog reduction, CI repair, repeated improvement passes | One loop iteration per run, with notes file and stop conditions |
| `resume` | Re-entering a prior session with the same objective | Prefer when the session already contains hard-won context |
| `parallel-dag` | Large RFC-driven work split into real dependency layers | Start with decomposition, then execute one ready layer at a time |

Use the helper script for all four patterns. For `parallel-dag`, treat the generated commands as orchestration scaffolding for decomposition, one-layer execution, and merge review rather than a full autopilot.

## Cross-CLI Rules

- Keep the loop contract stable even when the CLI changes: task, notes file, verification gate, and exit rule should stay recognizable.
- Do not assume permission models are interchangeable. Codex has explicit sandbox and approval flags; Claude and OpenCode need their own environment-specific controls.
- Do not assume session resume semantics are interchangeable. Some CLIs continue the last session, others resume a named session, and some can fork while continuing.
- Do not assume the current directory is a Git root. In this repository, Codex examples often need `--skip-git-repo-check`.

## Guardrails

- Do not run an unattended loop without `max-runs`, a completion signal, or a human review checkpoint.
- Do not retry the same failure without feeding the next run the actual failure context.
- Do not let the same pass both author and approve complex changes if an independent review pass is feasible.
- Do not store giant transcripts in the notes file. Keep only progress, blockers, verification status, and next-step cues.
- Do not claim a loop is safe just because one CLI supports sandboxing. Match the guardrails to the actual runner.

## Notes File Contract

Keep the bridge file compact and append-friendly. A good default shape is:

```markdown
## Progress
- [x] Added request validation
- [ ] Still missing retry handling

## Verification
- Passed: targeted unit tests
- Pending: full lint and integration suite

## Next Step
- Continue from the retry branch and reuse the new fixtures
```

## Helper Script

Use `scripts/render_loop_command.py` to generate copy-ready starter commands for `claude`, `codex`, or `opencode`.

Examples:

```bash
python scripts/render_loop_command.py --cli claude --pattern sequential --task "Implement the approved queue worker fix"
python scripts/render_loop_command.py --cli codex --pattern iterative-pr --task "Reduce the open lint backlog" --model gpt-5.2
python scripts/render_loop_command.py --cli opencode --pattern resume --task "Continue the dashboard cleanup" --json
python scripts/render_loop_command.py --cli codex --pattern parallel-dag --task "Implement the approved RFC in dependency layers"
```

The helper is intentionally conservative. It generates one safe starter sequence at a time and leaves shell-level outer loops to the operator.

## Examples

**Sequential fix loop for Claude:**
```bash
python scripts/render_loop_command.py --cli claude --pattern sequential --task "Fix the auth middleware regression"
```

**Iterative PR loop for Codex:**
```bash
python scripts/render_loop_command.py --cli codex --pattern iterative-pr --task "Clear all ESLint warnings" --model gpt-5.2
```

## References

- Read `references/pattern-selection.md` to decide whether you need a sequential pass, an iterative loop, or a dependency-aware parallel plan.
- Read `references/cli-adapters.md` when the user asks for a specific CLI such as Claude Code, Codex CLI, or OpenCode.

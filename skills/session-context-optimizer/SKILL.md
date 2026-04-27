---
name: session-context-optimizer
description: |
  Use whenever you need to learn from strong local skills and build a concise, task-focused session context pack before planning or implementation. Make sure to use this skill whenever the user says "context", "session pack", "what skills should I use", "learn from examples", "best practices in this repo", or "how do we do things here" — even for narrow tasks that only need 2-3 examples. Also trigger when starting work on an unfamiliar repository and needing a quick orientation from existing skills, or when the user wants to avoid broad manual reading and focus on the most relevant patterns. Covers script-backed skills, doc-backed skills, and mixed repositories.
---

# Session Context Optimizer

Optimize the current session by learning from a small set of strong local examples, not by wandering through the whole repository.

Treat this skill as a narrowing and synthesis workflow. It does not replace repository indexing, project doc generation, or generic prompt rewriting.

## Adaptive Detection

Before building context, detect the session needs:

1. **Task clarity**: Is the current task specific (e.g., "add tests") or vague (e.g., "improve this repo")?
2. **Repository type**: Is this a skill collection, a single app, a monorepo, or a mixed codebase?
3. **Existing guidance**: Check for root `CLAUDE.md`, `AGENTS.md`, or `SKILL.md` files.
4. **Similar tasks**: Look for skills with related names or purposes.
5. **Time pressure**: Note if the user needs a quick answer or deep research.

Use these signals to tune the scan scope and example count.

## Workflow

1. Confirm the current task goal and what the session context needs to support.
2. Read the repository root guidance and user-provided repo instructions first.
3. Run the helper script before broad manual reading:

```bash
uv run --python 3.11 scripts/build_session_context.py --root <repo>
```

If the current task is already clear, pass it to the helper:

```bash
uv run --python 3.11 scripts/build_session_context.py --root <repo> --task "<current-task>"
```

4. Read the JSON output first. Use the Markdown output only for human-facing review.
5. Check whether the helper is in `structure-only` or `structure-plus-task` mode before trusting the ranking order.
6. Select 2 to 5 representative examples using [references/pattern-selection.md](references/pattern-selection.md).
7. Read only the highest-signal files from those examples, usually:
   - `SKILL.md`
   - `agents/openai.yaml`
   - one or two focused references
   - one helper script or one representative test when needed
8. Build the final response using [references/context-pack-contract.md](references/context-pack-contract.md).
9. If confidence is still weak, do one narrow follow-up scan using [references/scan-guardrails.md](references/scan-guardrails.md).

## Command Shapes

Default scan:

```bash
uv run --python 3.11 scripts/build_session_context.py --root <repo>
```

Narrow to likely examples:

```bash
uv run --python 3.11 scripts/build_session_context.py --root <repo> --include agents-team-builder --include build-project-fixer
```

Narrow with a task goal:

```bash
uv run --python 3.11 scripts/build_session_context.py --root <repo> --task "improve session context for a script-backed skill"
```

Render a quick Markdown review:

```bash
uv run --python 3.11 scripts/build_session_context.py --root <repo> --format markdown --limit 5
```

## What To Extract

From each selected example, focus on the patterns that actually help the current task:

- trigger precision,
- workflow clarity,
- focused references,
- script or test support,
- stable output contracts,
- honest guardrails,
- places where the module stays intentionally narrow.

Do not restate an example's entire contents. Extract only the parts that improve the current session.

When the helper is in `structure-plus-task` mode, use `matched_terms` and `why_recommended` as ranking evidence, not as final truth.

## Guardrails

- Do not expand into root `AGENTS.md` or `CLAUDE.md` generation. That belongs to other skills.
- Do not use this skill as a substitute for broad repository indexing or feature tracing.
- Do not pick examples only because they are large, recent, or familiar.
- Do not infer repository-wide conventions from `_tmp*`, `tmp`, caches, `node_modules`, or generated artifacts by default.
- Do not keep reading files once the session has enough context to proceed safely.
- Do not blur observed facts, inferred guidance, and unknowns into one summary.

## Output Standard

Always return:

- `Successful Patterns`
- `Session Context Pack`
- `Next Action Guide`

The final response must clearly separate:

- observed repository facts,
- inferred guidance based on selected examples,
- open questions or confidence gaps.

If the repository signals are weak, return the best partial context pack possible and name the next narrow read or question needed to continue.

## Examples

### Example 1: Default scan for orientation

```bash
uv run --python 3.11 scripts/build_session_context.py --root .
```

### Example 2: Task-focused context pack

```bash
uv run --python 3.11 scripts/build_session_context.py --root . --task "improve test coverage for script-backed skills"
```

## References

- Read [references/pattern-selection.md](references/pattern-selection.md) before choosing examples.
- Read [references/context-pack-contract.md](references/context-pack-contract.md) before writing the final response.
- Read [references/scan-guardrails.md](references/scan-guardrails.md) when the first pass is noisy, weak, or too broad.

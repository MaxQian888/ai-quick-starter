---
name: feature-call-chain-mapper
description: Generate structured Markdown and JSON feature call-chain reports for unfamiliar repositories by tracing likely entrypoints, symbols, imports, registrations, and cross-module handoffs. Use when Codex needs to locate where a feature lives, map how a request or capability flows through a codebase, identify candidate entry files or handlers, or produce parseable call-chain documentation instead of freeform prose.
---

# Feature Call Chain Mapper

Trace the feature first, explain second. Use this skill when the user wants a stable call-chain artifact, not a prose-only summary.

## Start Here

1. Confirm the repository root and the exact feature question.
2. Choose the best anchor:
   - Use `--feature` when the user names a capability such as `login`, `export excel`, or `payment callback`.
   - Use `--entry-file` when the user already knows the likely file and wants the downstream path.
   - Use `--entry-symbol` when the user already knows the handler or function name.
3. Run the tracer before opening many files:

```bash
python scripts/build_feature_call_chain.py --root <repo> --feature "login"
```

4. Read the generated JSON or Markdown report before broad manual file reads.
5. Deepen only on the promoted files and handoffs.

If the request is only "map this repository" or "find what to read first", use `codebase-indexing-assistant` instead.

## Command Shapes

Default feature query:

```bash
python scripts/build_feature_call_chain.py --root <repo> --feature "login"
```

Explicit entry file:

```bash
python scripts/build_feature_call_chain.py --root <repo> --feature "login" --entry-file src/server.py
```

Narrow to a subtree:

```bash
python scripts/build_feature_call_chain.py --root <repo> --feature "login" --include src --exclude vendor
```

Stable output paths:

```bash
python scripts/build_feature_call_chain.py --root <repo> --feature "login" --markdown-out <report>.md --json-out <report>.json
```

## What To Read In The Report

- `candidate_entrypoints`: strongest file-level starting points.
- `evidence_files`: files that earned promotion through feature matches, symbols, or entrypoint signals.
- `symbols`: promoted functions or classes worth discussing explicitly.
- `nodes` and `edges`: the structured feature chain.
- `cross_module_handoffs`: where the chain crosses file boundaries.
- `blind_spots`: mandatory uncertainty notes.
- `suggested_next_reads`: the smallest set of follow-up files to inspect manually.

Read [references/output-schema.md](references/output-schema.md) when you need the exact Markdown sections or JSON fields.

## Workflow Rules

- Treat the generated chain as a heuristic map, not a complete semantic proof.
- Separate `observed` from `inferred` when you answer.
- Prefer the JSON output as the truth source; use the Markdown output for rendering and human review.
- If the report is noisy, rerun with `--include`, `--exclude`, or a more precise anchor instead of opening many unrelated files.
- If confidence is low, say so plainly and use `blind_spots` plus `suggested_next_reads` to define the next verification pass.

## Guardrails

- Do not claim the chain is complete unless you manually verified the missing dynamic and framework-driven edges.
- Do not turn the output into freeform prose that loses node, edge, confidence, or blind-spot structure.
- Do not ignore `blind_spots`; they are part of the deliverable.
- Do not broaden to repository-wide exploration when the user asked for one feature path.

## References

- Read [references/tracing-playbook.md](references/tracing-playbook.md) for anchor selection, narrowing, and follow-up rules.
- Read [references/output-schema.md](references/output-schema.md) for the Markdown and JSON contract.
- Read [references/blind-spots.md](references/blind-spots.md) for common failure modes and reporting language.

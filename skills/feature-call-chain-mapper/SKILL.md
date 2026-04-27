---
name: feature-call-chain-mapper
description: Use whenever tracing feature call chains, mapping execution paths, understanding unfamiliar code, analyzing runtime paths, or exploring how a specific capability flows through a codebase. Make sure to use this skill for code tracing, function call mapping, dependency chain analysis, feature exploration, or any request involving understanding how a feature works end-to-end. Also triggers for entrypoint discovery, cross-module handoff identification, or generating structured call-chain reports in Markdown and JSON.
---

# Feature Call Chain Mapper

Trace the feature first, explain second. Use this skill when the user wants a stable call-chain artifact, not a prose-only summary.

## Adaptive Detection

Before tracing, scan the workspace to understand the codebase structure:

1. Detect repository language and framework:
   - Look for `package.json` (Node.js), `Cargo.toml` (Rust), `go.mod` (Go), `pyproject.toml` (Python), `pom.xml` (Java).
   - Check for framework-specific entry patterns (Next.js pages, Flask routes, Express handlers).
2. Detect existing feature boundaries:
   - Search for feature-named directories (`features/`, `modules/`, `domains/`).
   - Look for API route files or controller files that may serve as entrypoints.
3. Detect test coverage:
   - Look for test files that may reveal feature entrypoints and expected flows.

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

## Examples

### Example 1: Tracing a Login Feature

**Input:** "How does login work in this repo?"

**Output:**
- Identifies entrypoint (e.g., `src/routes/auth.ts`).
- Maps chain through validation, database query, session creation.
- Lists cross-module handoffs and blind spots (e.g., middleware not statically traceable).

### Example 2: Narrowing to a Subtree

**Input:** "Trace the payment callback but only in the backend code."

**Output:**
- Uses `--include src/server --exclude src/client`.
- Focuses on webhook handler, payment service, and database updates.
- Explicitly notes excluded frontend code as a blind spot.

## Guardrails

- Do not claim the chain is complete unless you manually verified the missing dynamic and framework-driven edges.
- Do not turn the output into freeform prose that loses node, edge, confidence, or blind-spot structure.
- Do not ignore `blind_spots`; they are part of the deliverable.
- Do not broaden to repository-wide exploration when the user asked for one feature path.

## References

- Read [references/tracing-playbook.md](references/tracing-playbook.md) for anchor selection, narrowing, and follow-up rules.
- Read [references/output-schema.md](references/output-schema.md) for the Markdown and JSON contract.
- Read [references/blind-spots.md](references/blind-spots.md) for common failure modes and reporting language.

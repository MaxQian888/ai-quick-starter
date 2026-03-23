# Tracing Playbook

## Anchor Selection

- Use `--feature` when the user names a capability but not a concrete file or symbol.
- Add `--entry-file` when the likely file is known and you want the chain to start there.
- Add `--entry-symbol` when the user points at a specific handler or function.
- If the first pass is broad, rerun with narrower `--include` and `--exclude` filters instead of manually reading unrelated directories.

## Default Usage Pattern

1. Confirm the repository root.
2. Choose the smallest anchor that still captures the user question.
3. Run the tracer and inspect `candidate_entrypoints`, `edges`, `cross_module_handoffs`, and `blind_spots`.
4. Only then open promoted files for manual verification.

## When To Rerun

Rerun instead of broadening manual file reads when:

- too many evidence files appear,
- the feature term matches multiple subsystems,
- the top entrypoint is clearly wrong,
- the chain is low confidence,
- generated or vendor code is drowning the signal.

## Answering Rules

- Quote the path, symbol, and confidence for the main chain.
- Say explicitly which links are `observed` and which are `inferred`.
- If the chain is weak, lead with the uncertainty and list the best next files to inspect.
- If the user asked for a structured artifact, return the report paths or summarize using the same section structure.

## What This Tool Does Not Prove

- It does not guarantee runtime execution order.
- It does not fully resolve dynamic imports, reflection, dependency injection, or framework registration.
- It does not replace manual reading for high-risk edits.

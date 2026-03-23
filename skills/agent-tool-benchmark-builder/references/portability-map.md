# Portability Map

Use this guide when one benchmark must compare different agent runtimes.

## Neutral Benchmark Layer

Write tasks against a neutral schema first:
- request
- tool inventory
- argument contract
- expected primary call
- allowed alternatives
- scoring rules

This is the source of truth.

## Coding Agent Mapping

Typical shape:
- richer tool names
- tool arguments may be free-form text
- traces often include commentary plus calls
- environment state may be implicit in the workspace

Mapping advice:
- normalize commentary away from the judged trace
- convert shell-like or IDE-like calls into structured records before scoring
- record side effects separately when executable verification is needed

## Function-Calling Agent Mapping

Typical shape:
- explicit JSON schema
- strongly typed arguments
- parseability is a first-order metric
- traces may be shorter and cleaner

Mapping advice:
- preserve the neutral task intent
- keep strict parse validation
- use the same semantic argument rules as the coding-agent version

## Cross-Runtime Rules

- Compare on the same task semantics, not the same raw trace format.
- Keep the primary score focused on tool choice and required argument correctness.
- Add runtime-specific diagnostics as extra columns, not as the main score.
- If one runtime exposes richer tools than another, split the benchmark rather than forcing a fake apples-to-apples comparison.

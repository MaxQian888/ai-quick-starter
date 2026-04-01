# Workflow

Use this file when deciding how to split research work and how to merge it back into one tutorial package.

## Stage 1: Build The Input Brief

Write one short problem statement that captures:
- software name,
- target version or version window,
- target operating system or runtime,
- learner goal,
- and the expected depth.

Keep the brief narrow enough that all later claims can be attached to it.

## Stage 2: Dispatch Parallel Tracks

Run three tracks by default.

### Track A: Official Evidence

Focus on:
- official docs,
- official repositories,
- release notes,
- migration guides,
- and vendor-maintained examples.

Return structured findings with topic, claim, source, version, commands, and confidence notes.

### Track B: Community Evidence

Focus on:
- high-signal blogs,
- issue threads,
- discussion boards,
- trusted example repositories,
- and recurring troubleshooting patterns.

Return structured findings with the same fields as the official track.

### Track C: Case Design

Focus on:
- what the learner should build first,
- what the practical workflow should demonstrate,
- what failure case is worth teaching,
- and what files or snippets the tutorial package should include.

## Stage 3: Normalize Findings

Merge all track outputs into one shared brief before writing tutorial prose.

Use `scripts/build_research_brief.py` to:
- merge repeated facts,
- collect commands,
- list versions and platforms,
- capture verified claims,
- and preserve unresolved questions.

## Stage 4: Resolve Conflicts

If tracks disagree:
- prefer explicit conflict notes over silent cleanup,
- keep both sources attached,
- and downgrade certainty until the conflict is resolved.

## Stage 5: Build The Tutorial Outline

Use `scripts/build_tutorial_outline.py` only after the brief is coherent enough to support one tutorial path.

The outline should lock:
- section order,
- example sequence,
- checklist items,
- and support-material needs.

## Stage 6: Draft The Tutorial Package

Produce:
- the main tutorial,
- command snippets,
- config fragments,
- starter files or placeholders,
- and the verification summary.

Do not claim the tutorial is fully validated unless the critical path was actually run.

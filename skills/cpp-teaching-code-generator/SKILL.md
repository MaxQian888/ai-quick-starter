---
name: cpp-teaching-code-generator
description: Generate and revise instructional C++ code for lessons, demos, and practice tasks. Use when users ask for C++ teaching snippets, annotated walkthrough code, scaffolded exercises with TODOs, beginner/intermediate/advanced lesson variants, algorithm explanations with runnable source, or classroom-ready assignment starter code.
---

# C++ Teaching Code Generator

## Overview

Generate classroom-ready C++ code that stays runnable while teaching one clear objective.
Produce compact deliverables: code, explanation, exercises, and build/run commands.

## Core Workflow

1. Extract teaching targets.
- Identify topic, learner level, and requested format (demo, lab, assignment, project).
- Identify constraints: C++ standard, allowed libraries, input/output style, and runtime environment.
- Default to `C++17`, console I/O, and standard library only when details are missing.

2. Select a lesson pattern.
- Use [lesson-patterns.md](references/lesson-patterns.md).
- Choose one primary pattern:
  - `concept-demo`
  - `guided-implementation`
  - `bug-fix-lab`
  - `compare-approaches`
  - `mini-project`
- Keep one primary learning objective per artifact.

3. Generate teaching code.
- Keep the program compilable from start to finish.
- Write short comments that explain intent and trade-offs.
- Provide one runnable baseline before optimization variants.
- Include at least 2 practice tasks with explicit acceptance criteria.

4. Package output for teaching use.
- Return sections in this order:
  1. `Teaching Code`
  2. `How It Works`
  3. `Practice Tasks`
  4. `Build and Run`
- Include compile/run commands for the selected standard.
- Include one sample input/output pair when the program is interactive.

5. Validate quality before returning.
- Check [quality-checklist.md](references/quality-checklist.md).
- Eliminate hidden dependencies, undefined behavior traps, and unexplained constants.

## Scripted Scaffolding

Use `scripts/scaffold_cpp_lesson.py` to quickly generate repeatable lesson starters.

Example:

```bash
uv run scripts/scaffold_cpp_lesson.py ^
  --topic "vector and loop basics" ^
  --level beginner ^
  --pattern concept-demo ^
  --standard c++17 ^
  --output lessons/vector_loop_basics.cpp
```

The script writes a compilable `.cpp` starter with:
- metadata header
- pattern-specific runnable baseline
- level-specific practice TODO list
- build/run hints

Use `scripts/batch_scaffold_cpp_lessons.py` to generate multiple exercise starters by knowledge points.

Example (repeat `--topic`):

```bash
uv run scripts/batch_scaffold_cpp_lessons.py ^
  --topic "if else basics" ^
  --topic "for loop and accumulation" ^
  --topic "vector traversal" ^
  --level beginner ^
  --pattern guided-implementation ^
  --out-dir lessons/beginner-set
```

Example (`topics.txt`, one topic per line, supports `topic|level|pattern|standard|output`):

```bash
uv run scripts/batch_scaffold_cpp_lessons.py ^
  --topics-file topics.txt ^
  --out-dir lessons/mixed-set
```

## Fast Defaults

- Assume `beginner` when level is omitted.
- Prefer deterministic console output for teaching and grading.
- Prefer explicit loops and named variables for beginner cohorts.
- Defer advanced templates or metaprogramming unless requested.
- Preserve the user's explanation language; keep code identifiers in English unless asked otherwise.

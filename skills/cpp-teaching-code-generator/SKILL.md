---
name: cpp-teaching-code-generator
description: Use whenever generating, revising, or scaffolding instructional C++ code for lessons, tutorials, coding demos, practice exercises, lab assignments, classroom walkthroughs, algorithm explanations, or student starter code. Make sure to use this skill for beginner through advanced C++ topics, coding interview prep, scaffolded exercises with TODOs, runnable algorithm walkthroughs, or any request involving teaching C++17/20/23 concepts. Also triggers for requests about CMake build setups for teaching, multi-file lesson projects, or generating batch exercise sets.
---

# C++ Teaching Code Generator

## Overview

Generate classroom-ready C++ code that stays runnable while teaching one clear objective.
Produce compact deliverables: code, explanation, exercises, and build/run commands.

## Adaptive Detection

Before generating, scan the workspace to adapt output:

1. Detect project type and build system:
   - Look for `CMakeLists.txt`, `Makefile`, `compile_commands.json`, or `.vscode/tasks.json`.
   - If none exist, default to single-file `g++` or `clang++` compile commands.
2. Detect existing C++ standard:
   - Check `CMakeLists.txt` for `CMAKE_CXX_STANDARD`.
   - Check `Makefile` for `-std=` flags.
   - Default to `C++17` when no signal is found.
3. Detect learner level from context:
   - Look at existing lesson files for complexity patterns.
   - Check `references/lesson-patterns.md` for the project's established patterns.
4. Detect allowed libraries:
   - If `<iostream>` and `<vector>` appear in existing files, assume standard library only.
   - If third-party headers appear, note them for consistency.

## Core Workflow

1. **Extract teaching targets.**
   - Identify topic, learner level, and requested format (demo, lab, assignment, project).
   - Identify constraints: C++ standard, allowed libraries, input/output style, and runtime environment.
   - Default to `C++17`, console I/O, and standard library only when details are missing.

2. **Select a lesson pattern.**
   - Use [lesson-patterns.md](references/lesson-patterns.md).
   - Choose one primary pattern:
     - `concept-demo`
     - `guided-implementation`
     - `bug-fix-lab`
     - `compare-approaches`
     - `mini-project`
   - Keep one primary learning objective per artifact.

3. **Generate teaching code.**
   - Keep the program compilable from start to finish.
   - Write short comments that explain intent and trade-offs.
   - Provide one runnable baseline before optimization variants.
   - Include at least 2 practice tasks with explicit acceptance criteria.

4. **Package output for teaching use.**
   - Return sections in this order:
     1. `Teaching Code`
     2. `How It Works`
     3. `Practice Tasks`
     4. `Build and Run`
   - Include compile/run commands for the selected standard.
   - Include one sample input/output pair when the program is interactive.

5. **Validate quality before returning.**
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

## Examples

### Example 1: Beginner Loop Concept Demo

**Input:** "Teach for loops to beginners with a hands-on example."

**Output:**
- A single `.cpp` file that prints a multiplication table.
- Comments explain initialization, condition, and increment.
- Two practice tasks: (1) modify the range, (2) add a nested loop for 2D output.
- Build command: `g++ -std=c++17 loops_demo.cpp -o loops_demo`

### Example 2: Algorithm Walkthrough for Intermediate Learners

**Input:** "Show how std::sort works with a custom comparator."

**Output:**
- Runnable code sorting a vector of structs by multiple fields.
- Inline comments on comparator logic and stability.
- Practice task: implement a stable secondary sort manually.

## Fast Defaults

- Assume `beginner` when level is omitted.
- Prefer deterministic console output for teaching and grading.
- Prefer explicit loops and named variables for beginner cohorts.
- Defer advanced templates or metaprogramming unless requested.
- Preserve the user's explanation language; keep code identifiers in English unless asked otherwise.

# C++ Lesson Patterns

## Quick Selector

- `concept-demo`: Introduce one concept with a minimal runnable example.
- `guided-implementation`: Provide starter code with TODO blocks for students.
- `bug-fix-lab`: Train debugging skills with a safe buggy snippet and a fixed baseline.
- `compare-approaches`: Show baseline vs optimized implementation and trade-offs.
- `mini-project`: Combine multiple concepts in a small practical task.

## Pattern Details

### concept-demo

Use when introducing a single concept for first exposure.

Deliver:
- Problem statement in 1-2 lines
- Minimal runnable code path
- Output walkthrough
- 2 short extension exercises

Keep:
- Less than 80 lines for beginner cohorts
- One core abstraction only

### guided-implementation

Use when students should write part of the solution.

Deliver:
- Starter function signatures
- Compilable baseline behavior
- TODO comments with exact requirements
- Acceptance criteria for each TODO

Keep:
- TODO steps independent and incremental
- One failing edge case explicitly called out for students to handle

### bug-fix-lab

Use when practicing diagnosis and correction.

Deliver:
- Non-compiling or logically broken snippet inside comments
- Correct runnable baseline outside comments
- Guided debugging questions

Keep:
- Bug type explicit (off-by-one, overflow, invalid index, etc.)
- Final fixed version simple enough to reason about in class

### compare-approaches

Use when teaching algorithmic trade-offs.

Deliver:
- Baseline implementation first
- Improved implementation second
- Time/space complexity summary
- Scenario guidance: when to choose each approach

Keep:
- Same input/output behavior for both approaches
- Profiling discussion optional, conceptual complexity mandatory

### mini-project

Use when consolidating several concepts at once.

Deliver:
- Clear scope with a tiny data model
- One complete happy path
- 3 upgrade tasks (validation, persistence mock, performance)

Keep:
- No external dependencies by default
- Single source file unless user requests project structure

## Level Tuning

### beginner

- Prefer loops, arrays/vectors, functions, and conditionals.
- Limit pointer arithmetic and advanced STL customization.
- Explain output step by step.

### intermediate

- Add algorithm library usage, structs/classes, and stronger edge-case handling.
- Introduce complexity analysis in plain language.

### advanced

- Add performance-oriented design choices and API-level trade-offs.
- Allow templates, iterators, and more abstract interfaces when requested.

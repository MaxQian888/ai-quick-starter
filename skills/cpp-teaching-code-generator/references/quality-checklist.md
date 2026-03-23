# C++ Teaching Quality Checklist

## 1. Compile Correctness

- Confirm code builds with `-Wall -Wextra -pedantic` for the targeted standard.
- Confirm includes match actual usage.
- Confirm no undefined behavior in baseline path.
- Confirm sample input/output matches program behavior.

## 2. Teaching Clarity

- Confirm one primary learning objective is stated.
- Confirm comments explain "why" rather than narrating every line.
- Confirm variable and function names are instructional and readable.
- Confirm unexplained magic constants are removed or documented.

## 3. Exercise Design

- Confirm at least 2 tasks include explicit acceptance criteria.
- Confirm task difficulty increases gradually.
- Confirm starter state is compilable before students edit.
- Confirm hints point to concept, not full final answer.

## 4. Scope Control

- Confirm baseline solution is shown before optimizations.
- Confirm advanced constructs appear only when requested.
- Confirm no unnecessary third-party libraries.
- Confirm artifact size matches learner level.

## 5. Safety and Robustness

- Confirm edge cases are handled (`empty`, `single item`, invalid input).
- Confirm integer divisions and casts are intentional.
- Confirm no unsafe memory usage for beginner-facing artifacts.
- Confirm deterministic output for grading scenarios unless randomness is a learning goal.

## 6. Response Packaging

- Confirm output uses: `Teaching Code`, `How It Works`, `Practice Tasks`, `Build and Run`.
- Confirm compile command and run command are included.
- Confirm explanation language matches user language preference.

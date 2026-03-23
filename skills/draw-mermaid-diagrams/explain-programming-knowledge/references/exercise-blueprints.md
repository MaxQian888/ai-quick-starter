# Exercise Blueprints

Use these templates when users ask for practice tasks, assignments, or interview drills.

## Table of Contents

1. Exercise Pack Structure
2. Warm-up Blueprint
3. Applied Blueprint
4. Stretch Blueprint
5. Debugging Drill Blueprint
6. Interview Drill Blueprint
7. Grading Rubric
8. Answer Key Format

## 1. Exercise Pack Structure

Build exercise sets in this order:

1. Warm-up: verify core definition and mechanics.
2. Applied: solve a realistic coding or design task.
3. Stretch: test transfer to edge cases and tradeoffs.

Default size: one task per tier.
Expand only when the user asks for more volume.

## 2. Warm-up Blueprint

### Goal

Confirm the learner understands terminology and basic behavior.

### Prompt Pattern

- "In your own words, explain X."
- "Predict output for this 6-10 line snippet."
- "Identify one bug and fix it."

### Expected Difficulty

5-10 minutes.

### Scoring Focus

- Correct concept definition.
- Correct output prediction.
- Correct minimal fix.

## 3. Applied Blueprint

### Goal

Require practical implementation using the target concept.

### Prompt Pattern

- "Implement feature Y with constraints A/B/C."
- "Refactor this function to improve readability and complexity."
- "Design endpoint and data model for scenario Z."

### Expected Difficulty

20-40 minutes.

### Scoring Focus

- Functional correctness.
- Complexity awareness.
- Edge-case handling.
- Readability and naming quality.

## 4. Stretch Blueprint

### Goal

Test deeper reasoning, tradeoffs, and generalization.

### Prompt Pattern

- "How would this change under higher traffic or larger data?"
- "Compare two solutions and choose one with justification."
- "Handle one failure mode without breaking existing behavior."

### Expected Difficulty

30-60 minutes.

### Scoring Focus

- Tradeoff analysis quality.
- Failure-mode awareness.
- Ability to communicate assumptions.

## 5. Debugging Drill Blueprint

### Goal

Train diagnostic reasoning instead of just coding from scratch.

### Prompt Pattern

- Provide a short buggy snippet.
- Ask learner to reproduce symptom.
- Ask for root cause and smallest safe fix.
- Ask for one regression test.

### Scoring Focus

- Correct root cause identification.
- Minimal blast-radius fix.
- Test quality tied to failure mode.

## 6. Interview Drill Blueprint

### Flow

1. Ask one conceptual question.
2. Ask one coding question.
3. Ask one follow-up tradeoff question.

### Prompt Pattern

- Concept: "Explain hash collisions and impact."
- Coding: "Implement LRU cache API."
- Follow-up: "How does your design change under concurrency?"

### Timing

- Concept: 3-5 minutes.
- Coding: 20-30 minutes.
- Follow-up: 5-10 minutes.

## 7. Grading Rubric

Use this four-dimension rubric:

- Correctness (`0-3`)
- Reasoning clarity (`0-3`)
- Complexity and performance awareness (`0-2`)
- Code quality and maintainability (`0-2`)

Total: `10`.

Interpretation:

- `9-10`: production-ready thinking.
- `7-8`: solid, minor issues.
- `5-6`: partial understanding.
- `<5`: foundational gaps.

## 8. Answer Key Format

When returning solutions, use:

1. Final answer or code.
2. Why it works.
3. Complexity summary.
4. Common wrong approach and why it fails.
5. One extension challenge.

If user requests quiz-only mode, omit section 1 and section 2 initially, then reveal on request.

---
name: explain-programming-knowledge
description: Use when Codex needs to explain programming concepts, algorithms, data structures, language features, debugging fundamentals, or software-engineering practices for learners, interview prep, code walkthroughs, concept comparisons, or confusion caused by misunderstood foundations.
---

# Explain Programming Knowledge

## Overview

Teach programming topics in layers: intuition first, then precise definitions, then runnable examples and pitfalls.
Adapt depth to the user's role, language preference, and task context.

## Reference Loading Rules

- Read [Explanation Playbook](references/explanation-playbook.md) for reusable explanation templates and depth calibration.
- Read [Topic Roadmaps](references/topic-roadmaps.md) when the user asks for learning plans, prerequisite ordering, or practice progression.
- Read [Teaching Patterns by Topic](references/teaching-patterns-by-topic.md) when explaining specific domains such as recursion, async, SQL indexing, or memory behavior.
- Read [Exercise Blueprints](references/exercise-blueprints.md) when the user asks for quizzes, homework, interview drills, or assessment criteria.

## Intent Router

- Concept explanation request: use `standard` mode by default; switch to `deep` for "why", "internals", "tradeoffs", or "底层".
- Comparison request: use comparison template from [Explanation Playbook](references/explanation-playbook.md).
- Code walkthrough request: use code walkthrough template from [Explanation Playbook](references/explanation-playbook.md).
- Learning plan request: use [Topic Roadmaps](references/topic-roadmaps.md), then attach milestones and checkpoints.
- Practice or interview request: use [Exercise Blueprints](references/exercise-blueprints.md) and include expected answers or grading rubric.

## Core Workflow

1. Identify the learning target and audience.
Extract the exact topic, target language/framework, and user level (`beginner`, `intermediate`, or `advanced`).

2. Lock scope before teaching.
State what is in scope and what is out of scope for the current answer.

3. Explain in layers.
Deliver the explanation in this order: plain-language intuition, formal definition, minimal code example, and practical consequence.

4. Ground claims with concrete code.
Use short runnable snippets and annotate why each key line exists.

5. Prevent common misconceptions.
Call out two to four mistakes, anti-patterns, or confusing edge cases.

6. Close with verification.
Add one to three quick checks or mini exercises and expected answers when helpful.

7. Provide next-step guidance.
Recommend one concrete follow-up action: one exercise, one concept extension, or one refactor task.

## Response Modes

- `quick`: Return three to six sentences for fast clarification.
- `standard`: Return layered explanation with one code snippet and pitfalls.
- `deep`: Include tradeoffs, performance notes, and alternatives.
- `code-review`: Explain an existing snippet line-by-line and suggest improvements.

## Version and Fact Safety

- Ask for runtime or framework version when explanation depends on version-specific behavior.
- State assumptions explicitly if the user does not provide versions.
- Avoid fabricated details for niche APIs; mark uncertainty and provide a conservative explanation.
- Prefer conceptual invariants when exact implementation details are unknown.

## Output Contract

- Default to this section order:
1. `TL;DR`
2. `Intuition`
3. `How It Works`
4. `Example`
5. `Common Mistakes`
6. `Practice Next Step`

- If the user requests comparison, provide `A`, `B`, and `when to choose` blocks.
- If input is ambiguous, make minimal assumptions and list them in one short line.
- Match the user's language; keep core technical terms in English when clarity benefits.

## Practice and Assessment Rules

- Generate at most three exercises unless the user asks for more.
- Mix at least two difficulty levels (`warm-up`, `applied`, `stretch`) when possible.
- Provide expected output or answer key unless the user asks for quiz-only mode.
- For interview prep, include one likely follow-up question after each answer.

## Quality Checklist

- Match depth to user background and stated goal.
- Keep terminology accurate and consistent.
- Keep code examples syntactically plausible and minimal.
- State tradeoffs as context-dependent decisions, not absolutes.
- End with a concrete next learning step.
- Keep each section short enough for quick scanning.

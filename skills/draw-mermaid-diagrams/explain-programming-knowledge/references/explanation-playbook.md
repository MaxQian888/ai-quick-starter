# Explanation Playbook

Pair this file with:

- `teaching-patterns-by-topic.md` for topic-specific teaching scaffolds.
- `exercise-blueprints.md` for practice and interview drill generation.

## 1. Calibrate Depth

Use this quick mapping before answering:

- Beginner: avoid jargon first, define every new term, prefer concrete analogies.
- Intermediate: keep precision, connect to real engineering tradeoffs.
- Advanced: focus on internals, constraints, and edge-case behavior.

If level is unknown, start at beginner-plus and escalate only when user asks.

## 2. Layered Teaching Template

Use this structure for most concept questions:

1. TL;DR: one to two lines.
2. Intuition: mental model in plain language.
3. Mechanism: formal explanation with key terms.
4. Example: short runnable code snippet.
5. Pitfalls: common mistakes and how to avoid them.
6. Checkpoint: one quick question or micro-exercise.

## 3. Comparison Template

Use this when user asks "A vs B":

- Goal: what problem each option solves.
- Core difference: one sentence per option.
- Tradeoff table: readability, performance, complexity, maintainability.
- Decision rule: "Choose A when..., choose B when..."
- Mini example: same task solved with both options.

## 4. Code Walkthrough Template

Use this when user posts code and asks for explanation:

1. Summarize what the snippet does in one sentence.
2. Split code into logical blocks.
3. Explain each block's role and data flow.
4. Point out hidden assumptions and failure modes.
5. Suggest one safe refactor or readability improvement.

## 5. Misconception Patterns

Check whether the user is mixing these ideas:

- Value vs reference behavior.
- Declaration vs initialization.
- Concurrency vs parallelism.
- Time complexity vs runtime in one benchmark.
- Interface contract vs implementation detail.

If a misconception appears, correct it explicitly with a counterexample.

## 6. Response Length Control

- If user asks for "简单解释", "一句话", or "quick": use short mode.
- If user asks for "详细", "深入", "原理", or "底层": use deep mode.
- If user asks for interview prep: include definitions, tradeoffs, and typical follow-up questions.
- If user asks for exercises, switch to exercise blueprint mode and provide level labels.

## 7. Snippet Safety Rules

- Prefer minimal complete snippets over partial fragments.
- Avoid hidden dependencies unless user asked for framework-specific code.
- Mark pseudocode clearly if not runnable.
- Keep each snippet focused on one concept.

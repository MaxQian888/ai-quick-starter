# Triage Checklist

Use this checklist before creating the benchmark pack.

## Scope

- What agent runtime is under test: coding agent, function-calling agent, or hybrid?
- What is the primary capability: tool choice, argument correctness, ordering, recovery, or end-to-end completion?
- Is the benchmark single-turn, multi-step, or multi-turn?

## Tool Surface

- Is every available tool described with a clear purpose?
- Does every tool have a parameter contract?
- Are forbidden or dangerous tools explicitly identified?
- Is "no tool should be called" a valid outcome for some tasks?

## Gold Signal

- Is there a verified reason the expected tool is correct?
- Are semantically equivalent arguments allowed?
- Are multiple valid tool choices possible? If so, are they captured as allowed alternatives?
- Are failure modes written down instead of implied?

## Comparability

- Does the benchmark need to compare coding agents and function-calling agents?
- If yes, has the task been written in a runtime-neutral schema first?
- Are scoring rules independent of vendor-specific trace formatting?

## Validity

- Does the prompt leak the answer?
- Does success depend on hidden environment state?
- Will the judge reward verbose but wrong traces?
- Does the result table preserve enough detail to diagnose failures later?

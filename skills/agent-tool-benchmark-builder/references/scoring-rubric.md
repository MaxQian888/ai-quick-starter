# Scoring Rubric

Default to a rubric that diagnoses tool behavior instead of only producing one binary pass rate.

## Default Dimensions

- `tool_choice`
  Did the agent choose the correct primary tool?
- `arg_correctness`
  Did it provide the required arguments with valid values?
- `call_format`
  Did the tool call follow the target runtime format?
- `misuse_penalty`
  Did the agent make unnecessary, forbidden, or speculative calls?

## Default Weights

Use these starting weights when the benchmark focuses on tool selection:

```yaml
tool_choice_weight: 0.5
arg_correctness_weight: 0.3
format_weight: 0.1
overcall_penalty_weight: 0.1
```

Adjust only when the user explicitly wants a different emphasis.

## Strict vs Tolerant

### Strict

Use for regression gates and close leaderboard comparisons.

- exact primary-tool match
- required arguments must be complete
- wrong ordering can fail the task
- unnecessary tool calls are penalized

### Tolerant

Use for cross-runtime comparisons or early exploratory evaluation.

- allow tool aliases or equivalent wrappers
- allow semantically equivalent argument values
- allow harmless extra fields
- still penalize obviously wrong or dangerous calls

## Abstention and Clarification

If the correct behavior is "do not call any tool" or "ask for clarification," score it explicitly. Do not fold those cases into generic task failure.

Recommended reason codes:
- `correct-abstain`
- `should-have-abstained`
- `correct-clarify`
- `should-have-clarified`

## Reporting

Always report:
- per-dimension scores
- overall score
- a short reason code list

If the benchmark is used to compare models, report both:
- macro average across tasks
- breakdown by failure mode

# Judge And Metrics

Use a judge that is deterministic, structured, and easy to audit.

## Judge Input

The judge should receive:
- the task definition
- the tool contract
- the observed trace or final tool call
- the scoring mode

Avoid hidden side channels such as internal notes or extra gold labels not represented in the task pack.

## Judge Output

Require JSON with fixed keys such as:

```json
{
  "task_id": "t001",
  "scoring_mode": "strict",
  "tool_choice_score": 1.0,
  "arg_score": 0.5,
  "format_score": 1.0,
  "penalty_score": 0.0,
  "final_score": 0.75,
  "reason_codes": ["wrong-arg-value"],
  "notes": "Correct tool, but required query argument was too broad."
}
```

## Core Metrics

- `tool_choice_accuracy`
  Fraction of tasks where the primary tool was acceptable.
- `required_arg_accuracy`
  Fraction of tasks where required arguments were complete and valid.
- `format_valid_rate`
  Fraction of calls parseable by the target runtime.
- `abstention_accuracy`
  Fraction of abstention or clarification tasks handled correctly.
- `average_penalty`
  Mean penalty from forbidden or unnecessary calls.

## Comparison Rules

- Use the same scoring mode across compared runs.
- Keep judge prompt and rubric fixed while comparing models.
- If coding agents and function-calling agents emit different traces, normalize them before judging.
- Record parse failures separately instead of silently scoring them as generic wrong answers.

## Judge Failure Smells

- The judge rejects obvious semantic equivalents.
- The judge rewards verbose traces even when the first call is wrong.
- The judge requires vendor-specific syntax in a cross-runtime benchmark.
- The judge uses reason text that cannot be aggregated later.

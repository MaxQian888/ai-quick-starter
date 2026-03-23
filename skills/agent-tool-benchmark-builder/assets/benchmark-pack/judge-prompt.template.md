# Judge Prompt Template

Score the agent trace for one benchmark task.

## Inputs

- `task_definition`: the benchmark task YAML object
- `tool_contract`: the tool schema YAML object
- `agent_trace`: the observed tool call trace or final tool call
- `scoring_mode`: `strict` or `tolerant`

## Rules

1. Score `tool_choice` based on whether the first acceptable primary tool was selected.
2. Score `arg_correctness` based on the required arguments in the task and tool contract.
3. Score `call_format` based on whether the call can be parsed by the target runtime.
4. Score `misuse_penalty` based on forbidden or unnecessary calls.
5. Use the task's allowed alternatives when scoring in tolerant mode.
6. Do not reward extra reasoning text if the tool call itself is wrong.

## Output

Return JSON only.

```json
{
  "task_id": "t001",
  "scoring_mode": "strict",
  "tool_choice_score": 0.0,
  "arg_score": 0.0,
  "format_score": 1.0,
  "penalty_score": 0.5,
  "final_score": 0.15,
  "reason_codes": ["wrong-tool", "overcalling"],
  "notes": "The agent used a file-edit tool before any discovery step."
}
```

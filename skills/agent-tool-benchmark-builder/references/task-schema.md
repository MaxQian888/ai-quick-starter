# Task Schema

Use this schema when writing benchmark tasks.

## Required Fields

- `benchmark_id`
  Stable identifier for the benchmark pack.
- `focus`
  The main capability under test.
- `task_id`
  Stable identifier for one task.
- `user_request`
  The exact prompt or request presented to the agent.
- `available_tools`
  Tool names exposed to the agent for this task.
- `expected.primary_tool`
  The main gold tool choice.
- `expected.required_args`
  Required argument names and expected values or constraints.
- `evidence.rationale`
  Why this tool and these arguments are correct.
- `failure_modes`
  Short failure labels to support aggregation.

## Strongly Recommended Fields

- `context`
  Relevant task state that is visible to the agent.
- `expected.allowed_alternatives`
  Equivalent calls or tool names that should not be penalized under tolerant scoring.
- `expected.forbidden_tools`
  Wrong tools that may look tempting and should be penalized.
- `expected.preconditions`
  Order or state requirements.
- `evidence.oracle_signals`
  Machine-checkable facts, expected records, or state diffs.

## Field Design Rules

- Keep `user_request` realistic. Do not write benchmarkese.
- Keep `available_tools` limited to what the agent can actually see.
- Use `required_args` for mandatory correctness and move softer expectations into judge logic.
- Write `failure_modes` as short reusable tags such as:
  - `wrong-tool`
  - `missing-required-arg`
  - `wrong-arg-value`
  - `speculative-call`
  - `overcalling`
  - `failed-to-abstain`

## Minimal Example

```yaml
benchmark_id: coding-agent-tool-choice
focus: tool-selection-and-arg-correctness
tasks:
  - task_id: t001
    user_request: "Find where the app defines the login redirect."
    context: "Repository is available locally. ripgrep is installed."
    available_tools:
      - search_code
      - run_tests
      - edit_file
    expected:
      primary_tool: search_code
      required_args:
        pattern: "login redirect"
      allowed_alternatives:
        - tool: search_code
          required_args:
            pattern: "redirect"
      forbidden_tools:
        - run_tests
        - edit_file
      preconditions: []
    evidence:
      rationale: "This is a discovery task. Search should come before any test run or edit."
      oracle_signals:
        - "first_tool=search_code"
    failure_modes:
      - wrong-tool
      - speculative-call
```

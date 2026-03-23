# Leakage And Validity

Run these checks before trusting the benchmark.

## Prompt Leakage

- Does the user request contain the tool name verbatim when that would not happen in reality?
- Does the tool description reveal the exact winning argument shape?
- Are the task names themselves giving away the answer?

## Environment Leakage

- Does the expected answer depend on hidden filesystem state, network state, or credentials?
- Are preconditions written explicitly?
- If the environment is not reproducible, does the task at least state the intended assumptions?

## Judge Leakage

- Does the judge prompt encode one brittle gold answer instead of a rule?
- Are valid equivalent arguments incorrectly rejected?
- Does the judge see more context than the evaluated agent saw?

## Dataset Quality

- Are there duplicate tasks with trivial wording changes?
- Are all tasks concentrated in one domain or one parameter shape?
- Are the tools too easy to distinguish because their names are overly descriptive?

## Score Validity

- Is the benchmark measuring tool choice, or is it secretly measuring prompt formatting?
- Are parse failures and semantic failures separated?
- Are abstention and clarification handled as first-class cases?
- Are extra calls penalized separately from primary-tool failure?

## Required Note

When handing off the benchmark, state:
- what the benchmark measures well
- what it does not measure
- what hidden assumptions still remain

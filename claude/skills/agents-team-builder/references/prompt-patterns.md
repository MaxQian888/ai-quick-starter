# Prompt Patterns

Use this file when the generated prompts or `developer_instructions` need refinement.

## Agent Assignment Prompt

```text
Use the <agent-name> agent to handle <scope>. Keep ownership clear, stay within the assigned write scope, and report blockers early.
```

## Explorer Prompt

```text
Use the explorer agent to map the relevant files, contracts, and likely risks for <scope>. Stay read-only and return only evidence-backed findings.
```

## Worker Prompt

```text
Use the worker agent to implement <scope>. Do not revert other agents' work. Validate touched files and report exact blockers.
```

## Reviewer Prompt

```text
Use the reviewer agent to check <scope> for regressions, missing tests, and unsafe assumptions. Findings first, then residual risk.
```

## Developer Instructions Pattern

Keep them short and role-specific:

- language expectation
- ownership boundary
- read-only vs write-capable behavior
- validation expectation
- escalation rule for blockers

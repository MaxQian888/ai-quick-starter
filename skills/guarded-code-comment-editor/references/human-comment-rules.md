# Human Comment Rules

Read this file before adding or rewriting comments.

## Keep Or Add Comments For

- Non-obvious intent.
- Edge-case handling.
- Invariants that other code depends on.
- Trade-offs or framework quirks.
- Shell or PowerShell behavior that is easy to break with a tiny change.

## Rewrite Or Delete Comments That

- Narrate obvious code flow.
- Repeat the symbol name without adding context.
- Use empty filler such as:
  - `This function handles...`
  - `Initialize the variable`
  - `Set the value`
  - `Return the result`
- Explain every line in a straightforward block.
- Sound like generated tutorial prose instead of repository-local working notes.

## Default Detail Level

Default to medium detail:

- explain why,
- explain what could go wrong,
- explain why the code is written this way,
- skip everything the reader can infer immediately from the syntax.

Only escalate to more detail when the logic is genuinely tricky or future maintainers could break it easily.

## Good vs Bad

Bad:

```ts
// This function handles the save operation.
// Initialize the variable.
const trimmed = value.trim();
```

Good:

```ts
// Trim early so downstream cache keys do not treat extra spaces as distinct values.
const trimmed = value.trim();
```

Bad:

```python
# Return the normalized job id.
return f"job:{job_id.strip()}"
```

Good:

```python
# Keep the prefix stable because another service parses this identifier from logs.
return f"job:{job_id.strip()}"
```

## Final Self-Check

- Does the comment earn its place?
- Does it use the repository's words instead of generic filler?
- Would a maintainer learn something non-obvious from it?
- If deleted, would understanding or safety meaningfully get worse?

If the answer is `no` to the last two questions, the comment probably should not stay.

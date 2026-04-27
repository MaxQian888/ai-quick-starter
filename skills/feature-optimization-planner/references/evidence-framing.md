# Evidence Framing

Use this file when writing the final report. It keeps the output honest about what was observed, what was verified, and what is still an inference.

## Evidence Levels

| Label | Use when | Example wording |
| --- | --- | --- |
| Observed | The claim comes from static file reads or direct code inspection | "Observed in `src/auth/store.ts`: retry logic is duplicated across two branches." |
| Verified | The claim comes from a command, test, browser run, or other direct execution | "Verified by `pnpm exec jest src/auth/...`: the empty-token path is uncovered." |
| Inferred | The claim is a reasoned conclusion from local evidence, but runtime proof is missing | "Inferred risk: this branch may leak listeners because subscription setup has no visible cleanup." |
| External guidance | The claim comes from official docs or current external sources | "Current React guidance recommends moving this derived computation out of render when it is repeated on every update." |
| Uncertain | The available evidence is too weak to assert the claim confidently | "Uncertain: authorization may be enforced upstream, but that check is outside the audited surface." |

## Safe Sentence Starters

- `Observed in <path>: ...`
- `Verified by <command or runtime check>: ...`
- `Inferred risk: ...`
- `According to <source>: ...`
- `Uncertain because ...`

## What To Avoid

- Do not write `this is broken` when you only have static hints.
- Do not write `tests are missing` unless you actually looked for the relevant test surface.
- Do not write `best practice is` without naming the source or at least the framework/library.
- Do not hide uncertainty behind confident language like `clearly`, `obviously`, or `definitely`.

## Recommended Finding Shape

```markdown
### Issue: Missing failure-path coverage in token refresh flow

Observed in `src/auth/token-service.ts`: the refresh path has three error branches.
Observed in `src/auth/token-service.test.ts`: only the success path is covered.
Inferred risk: regressions in retry and expired-token handling may go undetected.
External guidance: current framework docs recommend covering both success and failure branches around async state transitions.
```

## Recommended Summary Shape

Use this pattern in the executive summary:

- what was observed locally,
- what was actually verified,
- where external guidance indicates drift,
- what remains uncertain and could change the plan.

# Log Quality Rules

Use these rules to decide whether a log line should exist and what it should say.

## Good Reasons To Log

- Crossing an external boundary: HTTP, queue, database, filesystem, subprocess, RPC.
- Completing a meaningful state change: created, deleted, retried, skipped, failed, published.
- Handling an unexpected but recoverable condition.
- Capturing an actionable failure with enough context to debug it later.

## Weak Reasons To Log

- Repeating what the caller already logs one layer above.
- Printing every branch inside a simple pure function.
- Emitting an `info` log for a high-frequency loop or render cycle.
- Logging whole request or response bodies when a stable ID would do.
- Adding success logs for trivial helpers that already have error handling upstream.

## Message Checklist

- Name the operation or event.
- Include the smallest useful identifier.
- Keep wording consistent with nearby files.
- Avoid vague text such as `something went wrong` unless the error object already carries the detail.
- Prefer stable nouns and verbs over transient implementation details.

## Density Checklist

- Entry log only if the operation is long-running, externally visible, or expensive.
- Result log only if the outcome matters operationally.
- Intermediate logs only when they explain a branch that is otherwise hard to diagnose.
- If three nearby logs can be reduced to one structured summary, do that.

## Sensitive Data Checklist

Never log:

- access tokens
- refresh tokens
- passwords
- full cookies
- API keys
- private keys
- raw personal data dumps

If context is still needed, log a redacted summary or a stable identifier instead.

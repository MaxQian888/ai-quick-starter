---
name: guarded-log-editor
description: |
  Use this skill whenever you need to add, remove, or rewrite logs inside a specified directory while preserving the repository's existing logging conventions.
  Make sure to use this skill whenever the user asks to add logging, reduce noisy logs, unify log style, adjust log levels,
  make logs reasonable, or clean up instrumentation — even if they say "debug this", "trace that", or "log what's happening".
  Also trigger for requests like "add debug output", "remove console.log spam", "standardize logging", or "instrument this module".
  Covers winston, pino, log4js, bunyan, Python logging, slog, zap, logrus, and any custom wrapper.
---

# Guarded Log Editor

Modify logs conservatively. Match the framework, import style, logger acquisition pattern, and message style already used near the target directory before editing any file.

## Adaptive Detection

Before editing logs, detect the local logging landscape:

1. **Framework**: run the audit script to identify the dominant logging system (winston, pino, Python logging, etc.).
2. **Confidence level**: only proceed with broad edits if `selected_system.confidence` is high.
3. **Logger pattern**: note how loggers are imported, constructed, and named in nearby files.
4. **Density**: identify high-density files that may need reduction before adding new logs.
5. **Mixed patterns**: treat `mixed-patterns` or `needs-manual-read` as stop signs for broad edits.

## Workflow

1. Confirm the repository root and the target directory that may be edited.
2. Run `uv run --python 3.11 scripts/audit_logging_surface.py --root <repo-root> --target <target-dir> --json` to collect local framework, confidence, density, and safe-fix signals.
3. Read `selected_system.confidence`, `file_findings`, and `safe_fix_plan` before touching code.
4. Read representative files from the target directory plus the nearest shared logger/config helper if the target is sparse or confidence is low.
5. Choose the dominant local logging pattern and keep it. If the directory already mixes styles, converge toward the pattern that appears most often in the same layer instead of introducing a new framework.
6. Edit only the requested directory unless the user explicitly approves broader cleanup.
7. Re-check the changed files for duplicated logs, incorrect levels, placeholder wording, secret leakage, and framework drift.
8. Run the narrowest available verification for the touched package or files, then report what was and was not verified.

## Examples

**Add logs to a new payment handler:**
```bash
uv run --python 3.11 scripts/audit_logging_surface.py --root . --target src/payments/ --json
# Reuse the existing logger and message style; add one entry log and one result log.
```

**Reduce debug noise in a service directory:**
```bash
uv run --python 3.11 scripts/audit_logging_surface.py --root . --target src/services/ --json
# Remove redundant triplets and high-cardinality debug lines before adding new logs.
```

## Editing Rules

- Reuse the existing logger object, import path, wrapper, and structured-field shape from nearby files.
- If the target directory has no logs, inspect sibling files and shared logging helpers before adding any.
- Keep request IDs, task IDs, user IDs, filenames, route names, or operation names when the surrounding code already uses them.
- Prefer stable identifiers and short outcome summaries over dumping full payloads or large objects.
- Remove redundant "starting", "processing", and "finished" triplets when one or two logs already cover the state transition clearly.
- Do not add logs to tight loops, hot render paths, polling ticks, or pure formatting helpers unless the local convention already does that deliberately.
- Do not introduce a second logging library just because it is newer or easier.
- Treat `mixed-patterns` and `needs-manual-read` as stop signs for broad edits. Read those files manually before changing them.

## Level Rules

- `trace` or `debug`: Use for branch detail, temporary diagnostics, or high-cardinality context only when the existing framework already supports and uses it nearby.
- `info`: Use for durable lifecycle milestones, external I/O boundaries, important state transitions, or user-visible operations.
- `warn`: Use for degraded but recoverable behavior that merits attention.
- `error`: Use for failed work, dropped side effects, or exceptions that matter to operators or users.
- `fatal` or `critical`: Keep only when the surrounding codebase already uses a process-ending level and the code path truly matches it.

## Quantity Rules

- Prefer one log at operation entry only when the action is externally meaningful or long-running.
- Prefer one log at operation result when success or failure matters more than the internal steps.
- Keep multi-step flows readable: log the state change, not every trivial branch.
- Delete neighboring logs that repeat the same identifier and outcome with different wording.
- If the audit flags a file as high density, reduce duplicate `info` and `debug` lines before adding new ones.

## Message Rules

- Use the vocabulary already present in the target area.
- State what happened, what object or action it affected, and why the level is justified.
- Keep messages short enough to scan in production logs.
- Do not log secrets, tokens, credentials, raw cookies, private keys, or full personal data.
- Redact or summarize large payloads instead of printing them wholesale.

## References

- Read `references/framework-detection.md` before choosing which logger pattern to preserve.
- Read `references/log-quality-rules.md` before changing log counts, levels, or message wording.
- Read `references/output-schema.md` to interpret `selected_system`, `safe_fix_plan`, `forbidden_actions`, and `blind_spots`.

## Helper Script

Run:

```bash
uv run --python 3.11 scripts/audit_logging_surface.py --root <repo-root> --target <target-dir> --json
```

Use the audit to identify dominant frameworks, confidence, safe-to-touch files, level balance, and files that may already be too noisy. Treat the audit as evidence, not as an automatic rewrite plan.

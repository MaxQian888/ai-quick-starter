# Framework Detection

Use this order of evidence before editing logs:

1. Files inside the target directory.
2. Shared logger helpers imported by those files.
3. Sibling directories in the same feature layer.
4. Repository-wide logger config only when local evidence is weak.

## What To Preserve

- Logging library or wrapper: `logger`, `logging`, `slog`, `zap`, `tracing`, `ILogger`, and similar.
- Logger acquisition style: constructor, dependency injection, module singleton, hook, or helper function.
- Message shape: plain strings, printf-style templates, structured key-value fields, or object-first logging.
- Error handling pattern: `logger.error(err, "...")`, `logger.exception(...)`, `slog.Error(..., "err", err)`, and similar.
- Existing field names such as `requestId`, `taskId`, `workflowId`, `filePath`, `userId`.

## When The Directory Is Sparse

If the target directory has zero or near-zero logs:

1. Read the nearest shared logging helper or app bootstrap logger config.
2. Read one or two sibling files that already handle similar operations.
3. Copy the same import path and logger acquisition style.
4. Add the minimum logs needed for the requested observability gap.

## Mixed-Framework Rule

If the target directory already mixes multiple frameworks:

- Prefer the framework used by most files in that same directory.
- If one framework is clearly the project-standard wrapper and another is incidental `console` usage, converge toward the wrapper.
- Do not start a repo-wide migration inside a scoped log-edit request.

## Common Signals

- JavaScript or TypeScript:
  - `console.*`
  - `logger.info(...)`, `logger.error(...)`
  - `pino(...)`, `winston.createLogger(...)`, `debug(...)`
- Python:
  - `logging.getLogger(...)`
  - `logger.info(...)`, `logger.exception(...)`
  - `structlog.get_logger(...)`, `from loguru import logger`
- Go:
  - `log.Printf(...)`
  - `slog.Info(...)`
  - `zap.New...`, `logger.Info(...)`
- Rust:
  - `info!(...)`, `warn!(...)`, `error!(...)`
  - `tracing::info!(...)`
- Java or Kotlin:
  - `LoggerFactory.getLogger(...)`
  - `log.info(...)`, `logger.warn(...)`
- C#:
  - `ILogger<T>`
  - `_logger.LogInformation(...)`
  - `Serilog.Log.Information(...)`

# Safety And Operations

## Safety Rules

- Never clone, install, or launch third-party tooling automatically.
- Treat WeSpy, Camofox, and external APIs as optional dependencies that must already exist.
- Accept only `http` and `https` URLs from batch files or stdin.
- Keep batch outputs inside the chosen `--output-dir` by generating sanitized filenames from the source URL.

## Batch Mode

- Use `--batch <file>` for newline-delimited URLs.
- Use `--manifest <file>` for JSON or JSONL task definitions with per-item metadata such as `mode`, `output_name`, `tags`, and `enabled`.
- Use `--stdin` to read URLs from standard input.
- Use `--continue-on-error` when partial success is acceptable.
- Use `--output-dir <dir>` to write one file per URL plus `batch-summary.json`.
- Expect `results.jsonl` unless a custom `--results-file` is provided.
- Use `--resume` to skip tasks that are already marked successful in the results log.
- Use `--cache-dir <dir>` to avoid refetching identical task inputs.
- Use `--retry`, `--retry-delay`, `--jobs`, and `--rate-limit-ms` to make large batches more stable without disabling guardrails.

## WeSpy Rules

- Prefer `--wespy-path` for explicit local checkouts.
- `WESPY_PATH` is the non-CLI fallback.
- `--allow-wespy-import` is allowed only when the current interpreter already has a working `wespy` import.
- If WeSpy is unavailable, log that fact and continue down the fallback chain.

## Video Platform Limits

- YouTube and Bilibili support focuses on public page metadata, not authenticated or private content.
- Treat extracted counts and metadata as best-effort snapshots from public markup.
- `--limit` applies to channel, UP, playlist, and collection item lists.
- If structured parsing fails, fall back to the generic web fetch chain instead of forcing brittle scraping.
- Do not promise comments, live chat, login-gated content, age-restricted media, or geo-restricted playback data.
- Bilibili public APIs can return anti-crawler responses such as `-799`, `-352`, `-401`, or `412` pages. Treat these as environment or traffic constraints, not parser bugs.
- For Bilibili UP spaces, the current stable path is `card` plus signed `wbi` archive search. Unsigned archive endpoints are not reliable enough to treat as the main path.
- `--download-media` currently targets public Bilibili single-video pages only and writes files under the chosen `--download-dir`.
- The downloader uses page-embedded `window.__playinfo__` DASH URLs plus explicit `Referer` headers; it does not bypass login, geo, or platform restrictions.
- If no local ffmpeg is available, keep the downloaded video and audio streams as separate files and report that state instead of pretending they were merged.

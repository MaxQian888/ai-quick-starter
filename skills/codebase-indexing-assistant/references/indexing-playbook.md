# Indexing Playbook

## Reading Priority

Use this order unless the user asks for something narrower:

1. `summary.docs`
2. `summary.manifests`
3. `commands`
4. `entry_candidates`
5. `reading_order`
6. direct file reads

This keeps early answers anchored in onboarding and bootstrap evidence instead of implementation detail.

## Question Patterns

### How does the project start?

- Read the top README or architecture doc first.
- Read manifest files next for script and dependency clues.
- Inspect `commands` for likely developer entry commands.
- Open the top one or two `entry_candidates` only if the docs and manifests are insufficient.

### What should I read first?

- Start from `reading_order`.
- Prefer files with `importance=high` or `importance=medium`.
- If the generated order looks noisy, rerun with `--include` or `--focus` instead of reading low-value files.

### Where does feature X live?

- Rerun with `--focus <keyword>`.
- Compare the promoted files against `directories` to see which area appears to own the feature.
- Open the narrowest set of files that combine:
  - focus match,
  - strong role signal,
  - import clues,
  - nearby tests.

### Which directories matter?

- Use `directories` to find dense areas.
- Cross-check with `files` that have `importance=high` or `importance=medium`.
- Promote directories only when they contain both role signals and likely entry or manifest files.

## Narrowing Rules

- Prefer `--include` when the likely answer lives in one subtree.
- Prefer `--exclude` when generated or vendor content is drowning the signal.
- Prefer `--focus` when the question names a feature, integration, or domain term.
- If the first scan hits `limits`, rerun with tighter filters before reading more files manually.

## Blind Spots

- Import extraction is shallow and may miss framework registration or generated wiring.
- The script prefers conventional names, so unconventional bootstrap files may rank low.
- Multiple apps in one monorepo may require separate scans with `--include`.


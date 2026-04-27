# Analysis Playbook

## Source Priority

1. Current repository files and manifests.
2. Explicit docs passed with `--doc`.
3. Discovered roadmap/spec/plan docs.
4. Inferred optimization guidance.

## Scan Strategy

- Default to whole-repo scan only when no target is provided.
- Prefer `--target` for module-specific audits.
- Use `--include`/`--exclude` to avoid noisy directories.
- Use `--max-files` and `--max-docs` to keep output focused.

## Evidence Rules

- Every high-priority opportunity should include concrete evidence paths.
- Keep docs evidence separate from source evidence.
- If evidence is weak, lower confidence and include blind spots.

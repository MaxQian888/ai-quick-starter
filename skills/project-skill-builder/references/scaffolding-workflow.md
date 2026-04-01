# Scaffolding Workflow

## Inputs

Provide three concrete inputs before running the builder:

1. the repository root,
2. the generated skill name,
3. and the output directory where the new skill should be created.

Normalize the generated skill name to lowercase hyphen-case before treating it as final.

## Default Flow

1. Start from the repository root, not a nested feature folder, unless the user explicitly wants a package-scoped skill.
2. Run `python scripts/build_project_skill.py --project-root <repo> --skill-name <skill-name> --output-dir <dir>`.
3. Add `--include` or `--exclude` if the first scan is broader than the actual target.
4. Add `--force` only when you intentionally want to replace an older generated package with the same folder name.
5. Open the generated `CLAUDE.md`, then `references/project-map.md`, then `references/working-rules.md`.
6. Tighten the generated `SKILL.md` if the repo has terminology or constraints the first pass missed.

## Scope Rules

- Use `--include` when the target is one package, app, or service inside a large workspace.
- Use `--exclude` when temp, generated, or vendor folders still leak into the scan.
- Lower `--max-files` only when a first pass is too broad; otherwise prefer full repository truth.
- Do not use `--force` as a default. Keep overwrite explicit.

## Review Checklist

- Are the listed docs and manifests real?
- Are command hints repository-specific rather than generic guesses?
- Does the generated `CLAUDE.md` explain the generated package shape clearly?
- Do entrypoint and reading-order sections clearly read as heuristics?
- Does the generated skill describe when to use it in future sessions?
- Does the generated package help a later Codex instance start with less wandering?

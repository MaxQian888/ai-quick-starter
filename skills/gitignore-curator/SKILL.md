---
name: gitignore-curator
description: |
  Curate `.gitignore` and related ignore files with stack-aware, evidence-based rules.
  Make sure to use this skill whenever the user mentions `.gitignore`, ignore files, untracked files, generated artifacts,
  workspace cleanup, or wants to keep certain files out of version control — even if they don't use those exact words.
  Also use for non-git workspaces that need ignore rules, Docker context filtering, or when the user says things like
  "my repo is messy", "too many untracked files", "what should I ignore?", "clean up untracked files",
  or "hide these from git". Covers Docker `.dockerignore`, ESLint `.eslintignore`, Prettier `.prettierignore`,
  and `.npmignore` scenarios. Trigger on any request to audit, generate, update, or fix ignore rules.
---

# Gitignore Curator

Inspect a repository or workspace, figure out what generated and local-only artifacts are lying around, and add safe ignore rules with clear evidence. Work conservatively: explain first, then edit only when the user says go (or has already asked for a direct cleanup).

## Adaptive Detection

Before analyzing, detect the workspace shape:

1. **VCS type**: git repo (check for `.git/`) vs plain workspace.
2. **Stack signals**: look for `package.json`, `Cargo.toml`, `pyproject.toml`, `Dockerfile`, `.csproj`, `go.mod` to determine relevant ignore patterns.
3. **Existing ignores**: read `.gitignore`, `.git/info/exclude`, `.dockerignore`, `.eslintignore`, `.prettierignore`.
4. **Untracked files**: run `git status` in git repos to see what artifacts are already present.
5. **Target files**: determine whether the user cares about VCS ignore, Docker context ignore, or linter ignore rules.

## Workflow

1. **Find the workspace root.** If the path sits inside a git repo, use the git root. Otherwise treat the requested directory as a plain workspace.
2. **Read what's already there.** Check `.gitignore`, `.git/info/exclude`, and any other ignore files already present so you don't duplicate or contradict existing rules.
3. **Run the analysis script.**
   ```bash
   python scripts/gitignore_curator.py --project-root <path> --json
   ```
   This gives you detected stacks, candidate rules, and the evidence behind each one.
4. **Review the output.** Look at `candidate_rules`, `skipped_rules`, and their evidence. In a git repo, weigh `git status`, recent commit paths, existing rules, and whether matching files are already tracked. In a plain workspace, lean on what you can actually see — directory names, stack signals, and current ignore files.
5. **Propose the changes.** Group additions by `target_file`, explain why each rule fits there, and surface any skipped or ambiguous patterns so the user sees the full picture.
6. **Confirm before editing.** If the user asked for a review or proposal, pause for approval. If they explicitly asked you to "clean up", "fix", or "update" ignore files directly, you can apply after the analysis.
7. **Apply when authorized.**
   ```bash
   python scripts/gitignore_curator.py --project-root <path> --apply --json
   ```
8. **Double-check the result.** Look at the files that were touched and flag anything that still needs a human eye — no automation is perfect.

## Guardrails

- Only add rules for generated or local-only artifacts, and only when the repository itself provides evidence.
- Keep every existing user rule intact; append only what's missing.
- Route shared generated artifacts and local environment files to `.gitignore`.
- Route editor or OS noise (like IDE metadata) to `.git/info/exclude` when a git repo is available. In plain workspaces, send everything to `.gitignore` since `exclude` isn't an option.
- Only touch `.dockerignore`, `.eslintignore`, `.prettierignore`, or `.ignore` if the repo already uses them or Docker context is clearly relevant.
- If `.npmignore` exists, inspect it but treat it as higher risk — don't auto-add publishing filters without explicit user intent.
- Never add a pattern that would hide files already tracked by git.
- In non-git workspaces, stay extra conservative. Stick to cache, temp, build, virtualenv, and editor-noise patterns where the evidence is obvious.
- Never auto-ignore source directories, migrations, fixtures, examples, public assets, docs, deployment manifests, or business configuration files.
- Treat `.env.example`, `.env.sample`, and similar template files as commit-worthy unless the user says otherwise.
- Prefer exact observed filenames for local env files rather than broad wildcards, when that keeps the result safer.
- Only suggest `_tmp*`, `.tmp-tests/`, `.uv-cache*/`, `.uv-python/`, and similar scratch directories when they actually exist in the workspace.
- Do not run `git add`, `git commit`, or any other destructive git command as part of this skill.

## Examples

**Review and propose ignore rules:**
```bash
python scripts/gitignore_curator.py --project-root ./my-repo --json
```

**Apply after review:**
```bash
python scripts/gitignore_curator.py --project-root ./my-repo --apply --json
```

## Helper Script

`scripts/gitignore_curator.py` handles deterministic analysis and apply mode.

If plain `python` isn't available, fall back to `uv run --no-cache --python 3.11 ...` or a repo-local interpreter.

## Reference

Read `references/patterns.md` when you need safe default patterns, guidance on routing rules to the right target file, or the exclusion list that explains why certain paths should never be auto-ignored.

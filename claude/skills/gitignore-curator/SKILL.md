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

## Workflow

The script does the detection (VCS type, stack signals, existing ignore files, untracked files, secondary targets like `.dockerignore`). Your job is to run it, interpret the evidence, and make the call about what to apply.

1. **Run the analysis.**
   ```bash
   python scripts/gitignore_curator.py --project-root <path> --json
   ```
   On systems where `python` isn't on PATH, fall back to `uv run --no-cache --python 3.11 python scripts/gitignore_curator.py ...` or use the project's interpreter. The script uses only the standard library, so any 3.10+ Python works.

   The JSON payload exposes `is_git_repo`, `detected_stacks`, `candidate_rules` (with `confidence` and `evidence`), `skipped_rules` (often tracked-file conflicts the user must resolve), and the `inspected_ignore_files` it actually read.

2. **Review the candidates.** In a git repo, weigh `git status`, recent commit paths, existing rules, and whether matching files are already tracked. In a plain workspace, lean on observed directories, stack signals, and current ignore files. Always read the `evidence` field — a candidate without `git-status` or `observed-*` evidence is weaker than one with it.

3. **Propose the changes.** Group additions by `target_file` so the user sees which rules go to `.gitignore`, which to `.git/info/exclude`, and which to `.dockerignore` or other secondary targets. Surface every entry in `skipped_rules` — those are usually the interesting ones (tracked content, ambiguous patterns).

4. **Confirm before editing.** If the user asked for a review or proposal, pause for approval. If they explicitly said "clean up", "fix", or "update" the ignore files, you can apply right after the analysis.

5. **Apply when authorized.**
   ```bash
   python scripts/gitignore_curator.py --project-root <path> --apply --json
   ```
   This appends only missing patterns under a `# Added by gitignore-curator` marker, never rewriting existing user rules.

6. **Double-check the result.** Look at the files that were touched and flag anything that still needs a human eye — no automation is perfect.

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

## Reference

Read `references/patterns.md` when you need safe default patterns, guidance on routing rules to the right target file, or the exclusion list that explains why certain paths should never be auto-ignored.

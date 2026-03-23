---
name: gitignore-curator
description: Inspect a git repository and update `.gitignore` plus related ignore files conservatively. Use when the user asks to review, repair, or refresh ignore rules based on current `git status`, recent commits, generated artifacts, local environment files, or repository-specific ignore files such as `.git/info/exclude` and `.dockerignore`.
---

# Gitignore Curator

Inspect the current git project, explain safe ignore-rule additions with evidence, and update the target ignore files only after the user confirms.

## Workflow

1. Confirm the target path is inside a git repository. Stop if it is not.
2. Read the existing `.gitignore`, `.git/info/exclude`, and any already-present related ignore files before proposing anything new.
3. Run `scripts/gitignore_curator.py --project-root <path> --json` to inspect detected stacks, candidate rules, and reasons.
4. Review `candidate_rules`, `skipped_rules`, and the evidence fields. Base your judgment on current `git status`, recent commit paths, existing ignore rules, and whether the repo already tracks matching files.
5. Group the proposed additions by `target_file`, explain why each rule belongs there, and call out skipped or ambiguous patterns. Ask for confirmation before editing any ignore file.
6. After confirmation, run `scripts/gitignore_curator.py --project-root <path> --apply --json`.
7. Re-check `git status`, inspect the touched ignore files, and call out anything that still needs human judgment.

## Guardrails

- Add only generated or local-only artifacts backed by repository evidence.
- Preserve existing user rules and append only missing lines.
- Prefer `.gitignore` for shared generated artifacts and local environment files.
- Prefer `.git/info/exclude` for editor or OS-specific local noise that should stay machine-local.
- Extend into `.dockerignore`, `.eslintignore`, `.prettierignore`, or `.ignore` only when the repository already uses them or there is direct Docker context evidence.
- Inspect `.npmignore` if it exists, but treat it as higher risk and avoid auto-adding rules there unless the user explicitly asks.
- Never add a pattern that would hide files already tracked by git.
- Do not auto-ignore source directories, migrations, fixtures, examples, public assets, docs, deployment manifests, or business configuration.
- Treat `.env.example`, `.env.sample`, and similar template files as commit-worthy unless the user explicitly says otherwise.
- Prefer exact local environment filenames observed in the repo instead of broad wildcard rules when that keeps the result safer.
- Do not run `git add`, `git commit`, or any destructive git command as part of this skill.

## Helper Script

Use `scripts/gitignore_curator.py` for deterministic analysis and apply mode.

Recommended commands:

```bash
python scripts/gitignore_curator.py --project-root . --json
python scripts/gitignore_curator.py --project-root . --apply --json
```

If plain `python` is unavailable in the current environment, use `uv run --python 3.11 ...` or a repo-local interpreter instead.

## Reference

Use `references/patterns.md` when you need safe default patterns, target-file routing guidance, or exclusion rules that explain why some paths must never be auto-added to ignore files.

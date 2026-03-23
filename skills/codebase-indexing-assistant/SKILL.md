---
name: codebase-indexing-assistant
description: Build temporary Markdown and JSON repository maps for large or unfamiliar codebases, then use them to guide code navigation, entrypoint discovery, setup-command hints, dependency tracing, and targeted file reading. Use when users ask to understand a project, map project structure, find where to start reading, locate likely entry files, identify key manifests or README files, trace a feature path, or narrow down a broad repository before deeper analysis.
---

# Codebase Indexing Assistant

Index first, read selectively second. Use the generated report to narrow what to inspect instead of wandering through the repository.

## Workflow

1. Confirm the repository root and the concrete question you need to answer.
2. Run the indexer before opening many files:

```bash
python scripts/build_code_index.py --root <repo>
```

3. Read the Markdown summary and JSON output paths printed by the script.
4. Use these fields before opening source files:
   - `summary.docs`
   - `summary.manifests`
   - `commands`
   - `entry_candidates`
   - `reading_order`
5. Open only the smallest file set needed to answer the question.
6. If the first pass is too broad, rerun with `--include`, `--exclude`, or `--focus` instead of scanning the entire repository again.
7. Separate observed facts from heuristic guesses when you answer.

## Common Command Shapes

Use temporary outputs by default:

```bash
python scripts/build_code_index.py --root <repo>
```

Narrow to a subtree:

```bash
python scripts/build_code_index.py --root <repo> --include src --include docs
```

Focus on one feature:

```bash
python scripts/build_code_index.py --root <repo> --focus auth
```

Write explicit output files when another step needs stable paths:

```bash
python scripts/build_code_index.py --root <repo> --markdown-out <report>.md --json-out <index>.json
```

## Answering Playbook

- For "How does this project start?": read `summary.docs`, `summary.manifests`, `commands`, then `entry_candidates`.
- For "What should I read first?": start from `reading_order`, then justify any extra files you open.
- For "Where is feature X?": rerun with `--focus <keyword>`, then inspect the promoted files and their import clues.
- For "What owns this part of the codebase?": use `directories` and high-importance `files` records before opening implementation files.

## Guardrails

- Do not treat `entry_candidates` or `reading_order` as facts. They are heuristics.
- Do not claim a command works unless you actually ran it.
- Do not keep broadening manual file reads when the index says you should rerun with narrower filters.
- Do not use this skill as a substitute for semantic debugging or build repair.

## References

- Read `references/indexing-playbook.md` for narrowing strategy and question-driven usage.
- Read `references/output-schema.md` for the Markdown sections and JSON fields the script emits.


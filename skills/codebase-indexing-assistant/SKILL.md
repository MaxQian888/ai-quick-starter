---
name: codebase-indexing-assistant
description: >
  Use this skill whenever you need to orient yourself in a large, unfamiliar, or complex codebase before making targeted changes.
  Make sure to use it when you are onboarding to a new repository, searching for entrypoints, trying to understand project structure, or deciding which files to read first.
  Covers heuristic repository scanning, manifest detection, command extraction, entrypoint suggestion, reading-order generation, and focused keyword-based narrowing for any language or framework.
---

# Codebase Indexing Assistant

Index first, read selectively second. Use the generated report to narrow what to inspect instead of wandering through the repository.

## Adaptive Detection

Before indexing, scan for:
- Repository root and primary language indicators (`package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `pom.xml`)
- Monorepo signals (`pnpm-workspace.yaml`, `nx.json`, `Cargo.toml` workspace, `go.work`)
- Documentation files (`README.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`)
- The concrete question you need to answer to set `--focus` or `--include` filters
- Whether the repo is large enough (>1000 files) to warrant `--exclude` for `node_modules`, `dist`, `.git`

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

## Examples

**Example 1: Orient yourself in a new repository**
```
User: "I just cloned this repo. What should I read first to understand it?"
Agent: Run `python scripts/build_code_index.py --root .`, read `summary.docs`, `summary.manifests`, `commands`, and `reading_order`, then present a justified reading list.
```

**Example 2: Find where authentication lives**
```
User: "Where is the auth logic in this codebase?"
Agent: Run `python scripts/build_code_index.py --root . --focus auth`, inspect promoted files and import clues, and report the likely auth module locations with heuristic confidence.
```


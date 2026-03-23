---
name: project-ai-context-initializer
description: Use when initializing or refreshing project AI context for a repository, especially when Codex needs to scan a codebase, generate root-level and module-level AGENTS.md or CLAUDE.md files, add Mermaid structure maps and breadcrumb navigation, or report which modules were scanned versus skipped.
---

# Project AI Context Initializer

## Overview

Initialize repository-facing AI context with a concise root document and a small set of deeper module documents.

Treat subagents as the primary scanning surface. Use local helper scripts only inside those subagent runs or as a deterministic fallback for inventory summaries.

## Start Here

1. Confirm the target repository root and the project summary.
2. Create or refresh a timestamp by dispatching a dedicated datetime subagent first.
3. Dispatch a second subagent to perform the repository scan and draft the documentation set.
4. Integrate the resulting docs locally, then print a coverage summary in the main conversation.

## Required Workflow

### 1. Get Timestamp First

Dispatch a datetime-only subagent before any architecture scan.

In Claude-style environments, the user may describe this as a `Task` call. In Codex, adapt that to the native subagent tools while preserving the same sequence.

The subagent should return one timestamp string suitable for doc metadata.

### 2. Dispatch The Initializer Architect

Dispatch a second subagent with:
- the project summary,
- the timestamp,
- the repository root,
- the requirement to produce a root context doc and a small set of module docs,
- and the rule that generated or temporary directories must be skipped unless they are needed for explanation.

Tell the architect to work in four phases:
1. inventory,
2. module prioritization,
3. targeted deep reads,
4. doc drafting.

If a local inventory script is helpful, let the architect run:

```bash
python scripts/scan_project_context.py --root <repo>
```

Read the structured output first, then deepen only where the report shows high-value modules.

### 3. Write Root And Module Docs

Create or refresh:
- one root `AGENTS.md`,
- one root `CLAUDE.md`,
- and a small set of module-level `CLAUDE.md` files.

Default to 3-8 module docs. Favor modules that are:
- primary entrypoints,
- representative examples,
- important docs hubs,
- or high-signal implementation seams.

Do not try to create a module doc for every directory in a large mono-repo or skill collection. The goal is navigation, not duplication.

### 4. Include The Required Doc Features

Every root or module doc should include:
- a short purpose statement,
- breadcrumbs,
- a Mermaid structure diagram,
- key files or directories,
- read order,
- skip notes when relevant,
- and a small number of concrete next places to inspect.

Use the templates in [assets/templates/root-agents.md](assets/templates/root-agents.md), [assets/templates/root-claude.md](assets/templates/root-claude.md), and [assets/templates/module-claude.md](assets/templates/module-claude.md) as starting points, not rigid output.

### 5. Print The Coverage Summary In Main Chat

After the docs are written, print a compact summary with:
- root document status,
- identified modules,
- scanned versus total counts,
- coverage percentage,
- skipped reasons,
- generated diagram count,
- and recommended next scans.

Use the summary contract in [references/doc-contract.md](references/doc-contract.md).

## Guardrails

- Do not modify source code or repository behavior.
- Do not index `node_modules`, `dist`, binary assets, `.git`, temp fixtures, `.tmp*`, or cache directories unless they are directly relevant.
- Do not claim full-repo coverage when only the main seams were reviewed.
- Do not let module docs drift away from real file names or actual entrypoints.
- Do not replace an existing high-quality root doc with a lower-signal rewrite; merge incrementally instead.
- Do not hide skipped areas. Name them explicitly in the summary.

## Selection Rules

- Read [references/module-selection.md](references/module-selection.md) before deciding which subdirectories deserve their own `CLAUDE.md`.
- Read [references/doc-contract.md](references/doc-contract.md) before drafting or updating docs.
- Read [references/workflow.md](references/workflow.md) when you need the exact subagent sequence or a Codex-vs-Claude adaptation note.

## Output Standard

The preferred output set is:
- root `AGENTS.md` as the main human and agent entrypoint,
- root `CLAUDE.md` as an alternate discovery surface,
- targeted module-level `CLAUDE.md` files,
- and a main-chat summary that reports coverage honestly.

If the repository already standardizes on only one root agent file, reuse that pattern and make the second root file a thin redirect.

---
name: project-ai-context-initializer
description: >
  Use this skill whenever you need to initialize, refresh, or update AI-facing documentation for a repository.
  Make sure to use it when the user wants to create AGENTS.md or CLAUDE.md files, add navigation maps, document project structure for AI assistants, or generate module-level context docs with Mermaid diagrams and breadcrumbs.
  Covers subagent-driven repository scanning, root and module doc generation, coverage reporting, and incremental updates for mono-repos and multi-module projects.
---

# Project AI Context Initializer

## Adaptive Detection

Before initializing context, scan for:
- Existing root docs (`AGENTS.md`, `CLAUDE.md`, `README.md`) to decide between create and refresh
- Repository type (mono-repo, skill collection, single app, library) to set module selection strategy
- Generated or temporary directories to skip (`node_modules`, `dist`, `.tmp*`, `__pycache__`)
- Primary entrypoints and high-signal implementation seams for module doc candidates
- Whether the environment supports subagent dispatch (Claude Tasks, Codex native tools)

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

## Examples

**Example 1: Initialize context for a new repository**
```
User: "Can you generate AI context documentation for this repository so future agents can understand it faster?"
Agent: Dispatch a datetime subagent, then an architect subagent with the repo root, run `scripts/scan_project_context.py --root .` for inventory, generate root AGENTS.md and CLAUDE.md, create 3-8 module-level CLAUDE.md files with Mermaid diagrams, and print an honest coverage summary.
```

**Example 2: Refresh docs after major changes**
```
User: "We refactored the auth and payment modules. Can you update the context docs?"
Agent: Run the inventory script, identify affected modules, merge incremental updates into existing root and module docs, preserve high-quality unchanged sections, and report what was updated versus preserved.
```

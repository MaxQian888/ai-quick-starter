---
name: guarded-project-i18n-support
description: Use when planning or adding i18n support at repository or app scope, especially when Codex must inspect the existing stack first, choose a framework that fits the current project shape, avoid introducing a conflicting i18n system, and stage the rollout plus verification conservatively.
---

# Guarded Project I18n Support

## Overview

Inspect the repository first. Only recommend or implement project-level i18n support after the existing stack, application shape, and rollout risks are visible.

Use this skill for repo-wide or app-wide i18n enablement, not for a single component fix in isolation.

## Workflow

1. Confirm the repository root and the app surface that needs localization.
2. Run the planner before picking a framework:

```bash
uv run --python 3.11 scripts/build_project_i18n_plan.py --root <repo>
```

3. Read the JSON output first. Use the Markdown output for human review.
4. Check `recommended_strategy.mode`:
   - `extend-existing`: reuse the detected system only.
   - `introduce-new`: use the suggested system and rollout sequence only if the profile is coherent.
   - `blocked`: stop and resolve ambiguity before wiring i18n.
5. Follow `adoption_plan` in order. Do not skip bootstrap or verification steps.
6. Verify with the repository's real runtime or test stack. Do not claim success from the static plan alone.

## What To Read In The Report

- `project_profile`: runtime and framework evidence that constrains safe i18n choices.
- `selected_system`: the most likely existing i18n stack plus confidence and evidence.
- `recommended_strategy`: whether to extend, introduce, or block.
- `strategy_options`: fallback choices and why they were not selected first.
- `adoption_plan`: staged implementation steps for the chosen path.
- `verification_plan`: checks to run after wiring messages, providers, routes, and localized components.
- `forbidden_actions`: actions likely to create a second i18n system or break the app.
- `blind_spots`: gaps static analysis cannot prove.

## Decision Rules

- If the repository already has one dominant i18n stack, extend it instead of replacing it.
- If no stack exists, choose a system that matches the app shape:
  - Next.js app: prefer `next-intl`
  - React SPA or shared React surface: prefer `react-i18next`
  - Vue app: prefer `vue-i18n`
  - Python-only app or CLI: prefer `gettext`
- If the repository contains multiple UI frameworks, multiple candidate stacks, or a custom wrapper with unclear entrypoints, stop and gather more evidence before changing code.
- If only one app or package needs i18n, scope the rollout to that surface first instead of the whole repository.

## Guardrails

- Do not introduce a second provider, message tree, or locale registry when the repository already has one.
- Do not choose a framework only from package popularity. Use local app structure first.
- Do not bulk-convert every string in one pass. Wire the foundation, localize one representative flow, then expand.
- Do not normalize ambiguous mixed stacks without confirming the intended owner app.
- Do not claim the project is fully internationalized after adding only the bootstrap or dictionary layer.

## References

- Read [references/detection-playbook.md](references/detection-playbook.md) for signal order and stop conditions.
- Read [references/strategy-selection.md](references/strategy-selection.md) for framework selection and rollout choices.
- Read [references/output-schema.md](references/output-schema.md) for the report contract.
- Read [references/official-sources.md](references/official-sources.md) after the local stack is clear and you need framework-specific API details.

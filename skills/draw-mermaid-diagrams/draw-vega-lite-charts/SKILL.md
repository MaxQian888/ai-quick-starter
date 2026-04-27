---
name: draw-vega-lite-charts
description: Use when Codex needs to create, revise, or explain Vega-Lite chart specifications from natural-language chart requirements, data field mappings, or broken specs, including chart design, spec debugging, chart-type changes, and readability or interaction improvements.
---

# Draw Vega-Lite Charts

## Overview

Generate valid Vega-Lite specs quickly from user intent and data descriptions.
Start with a minimal runnable spec, then layer transforms and interactions safely.

## Reference Loading Rules

- Read [Vega-Lite Patterns](references/vega-lite-patterns.md) for chart skeletons and transform snippets.
- Read [Chart Selection by Question](references/chart-selection-by-question.md) when the user intent is analytical but chart type is unclear.
- Read [Debug Playbook](references/debug-playbook.md) when the user reports parse errors, blank charts, wrong values, or mixed aggregate issues.
- Read [Chinese Business Scenarios](references/chinese-business-scenarios.md) when the request is in Chinese and describes ecommerce, growth, or operations dashboards.
- Run `scripts/build-vega-lite-stub.js` when a deterministic starter spec is needed from structured field mappings.

## Core Workflow

1. Extract intent and data constraints.
Identify metrics, dimensions, comparison goal, time grain, and whether data is raw or pre-aggregated.

2. Choose chart pattern before coding.
Use [Chart Selection by Question](references/chart-selection-by-question.md) to choose a chart family, then use [Vega-Lite Patterns](references/vega-lite-patterns.md) to finalize channel mapping.

3. Draft minimal valid spec first.
Start with `$schema`, `data`, `mark`, and `encoding`. Keep the first draft small and runnable.

4. Add detail incrementally.
Add `transform`, `tooltip`, `sort`, axis formatting, and legends only as needed.
Use `params` or layered specs when interaction or richer composition is requested.

5. Validate semantics.
Check field names, field types, aggregate/group-by coherence, and scale correctness.
If input is ambiguous, state assumptions briefly and continue with a best-fit draft.

## Deterministic Scaffold Workflow

Use this when user input already includes clear channel mappings and you want a stable initial JSON:

1. Build a small config JSON with `schemaUrl`, `data`, `mark`, `encoding`, and optional `transform`.
See example input: [stub-config-example.json](references/stub-config-example.json)
2. Run:
`node scripts/build-vega-lite-stub.js --config path/to/config.json --out path/to/spec.json`
3. Inspect output JSON and apply user-specific refinements manually.

## Output Contract

- Default to a single fenced `json` Vega-Lite spec.
- Keep field names exactly as the user provides.
- For unknown datasets, show a placeholder `data.url` and list required columns.
- For edits, preserve unchanged parts and modify only requested behavior.
- For multiple options, provide at most 2 variants with one-line tradeoffs.

## Debugging Rules

- Reproduce issues with the smallest possible spec.
- Check type mismatches first (`temporal`/`quantitative`/`nominal`/`ordinal`).
- Check aggregate logic next (avoid mixing aggregated and raw fields unintentionally).
- Temporarily remove `layer`, `facet`, or `params` to isolate parser or semantic errors.
- If runtime behavior is uncertain, return a conservative fallback spec that still answers the question.

## Quality Checklist

- `$schema` points to a Vega-Lite schema.
- Mark type and encodings match the analytical goal.
- Transform pipeline is minimal and ordered correctly.
- Axes, legends, and tooltips are readable.
- Output is valid JSON and copy-paste ready.
- Assumptions are explicit when source data is incomplete.

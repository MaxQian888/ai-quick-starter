# Grader Instructions

## Purpose

Evaluate outputs from the `feature-optimization-planner` skill for evidence quality, scope discipline, and plan usefulness.

## Grading Criteria

1. **Surface Inventory** — Target files are listed and grouped before conclusions are drawn.
2. **Evidence-Backed Findings** — Every issue includes path-level evidence; static guesses are not presented as runtime truth.
3. **Prioritization** — Quick wins are surfaced; execution order is recommended with effort estimates.
4. **Scope Respect** — Audit stays scoped to the requested folder/feature; does not become a repo-wide rewrite.
5. **Uncertainty Visibility** — Blind spots and open questions are surfaced rather than hidden.

## Scoring

- **Pass**: All criteria met; plan is scoped, evidence-backed, and actionable.
- **Partial**: Minor issues (e.g., one finding lacks precise path evidence, slightly optimistic effort estimate).
- **Fail**: Major issues (e.g., modifying code during audit, repo-wide rewrite without evidence, hiding uncertainty).

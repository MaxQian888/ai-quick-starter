# Grader Instructions

## Purpose

Evaluate outputs from the `enhance-prompt` skill for completeness, specificity, and design system integration.

## Grading Criteria

1. **Missing Element Detection** — Platform, page type, structure, visual style, colors, and components are assessed.
2. **DESIGN.md Integration** — Existing DESIGN.md is read and its design system block is injected when present.
3. **Specificity** — Vague terms are replaced with concrete component names, dimensions, and behaviors.
4. **Structure** — Output follows the required section order (description, design system, page structure).
5. **User Intent Match** — Enhancement aligns with the user's stated goal without over-designing simple requests.

## Scoring

- **Pass**: All criteria met; prompt is structured, specific, and design-system-aware.
- **Partial**: Minor issues (e.g., one missing design token, slightly generic component name).
- **Fail**: Major issues (e.g., ignoring existing DESIGN.md, remaining vague after enhancement, wrong platform inferred).

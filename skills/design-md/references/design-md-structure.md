# DESIGN.md Structure and Quality Checklist

Use this schema to keep generated outputs stable and reusable across Stitch prompts.

## Required Structure

```markdown
# Design System: [Project Title]
**Project ID:** [Project ID]

## 1. Visual Theme & Atmosphere
- Describe mood, density, and visual intent.
- Use concrete language grounded in observed UI evidence.

## 2. Color Palette & Roles
- List each key color with:
  - Descriptive semantic name
  - Exact hex code (or rgba)
  - Functional role in the interface

## 3. Typography Rules
- Summarize font families, hierarchy, weights, spacing, and readability strategy.
- Separate heading/body/meta behavior when possible.

## 4. Component Stylings
- Buttons
- Cards/containers
- Inputs/forms
- Navigation (when visible)
- For each: shape, color behavior, depth/shadow, and interaction hints.

## 5. Layout Principles
- Explain spacing rhythm, grid logic, alignment, and responsive behavior.
```

## Writing Guidance

- Prefer semantic descriptions over raw utility classes.
- Keep technical precision in parentheses after natural-language phrasing.
- Use consistent naming for recurring tokens.
- Mark unknown or ambiguous points explicitly instead of guessing.

## Quality Checklist

Before finishing, verify all items:

- [ ] The document includes all five required sections in order.
- [ ] Key colors include semantic name + hex/rgba + role.
- [ ] Typography describes hierarchy, not only font names.
- [ ] Component descriptions mention behavior and visual traits, not just labels.
- [ ] Layout section reflects actual spacing/alignment patterns from evidence.
- [ ] No fabricated business metrics, data points, or unsupported claims.
- [ ] Language is concise and reusable in future Stitch prompts.

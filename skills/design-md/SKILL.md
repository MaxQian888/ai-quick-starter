---
name: design-md
description: Use whenever generating or refreshing a DESIGN.md for Stitch projects, capturing design systems, documenting visual languages, extracting design tokens from screens, or ensuring UI consistency across multiple generated pages. Make sure to use this skill for any request involving Stitch design documentation, color palette extraction, typography hierarchy documentation, component style guides, or creating reusable design specs from existing screens. Also triggers for design system initialization, visual language standardization, or converting screenshots into structured design documentation.
---

# Design MD (Stitch)

Create a reusable `DESIGN.md` that captures a Stitch project's visual language in natural design terms plus exact values.

## Adaptive Detection

Before creating the design document, scan the workspace to understand the project context:

1. Detect existing design documentation:
   - Look for existing `DESIGN.md`, `.stitch/DESIGN.md`, or `design-system.md` files.
   - Check for design token files (`tokens.json`, `theme.js`, `colors.css`).
2. Detect Stitch project context:
   - Look for `.stitch/` directories or Stitch configuration files.
   - Check for existing screen exports or HTML code downloads.
3. Detect related skills:
   - If the user also needs prompt enhancement, coordinate with the `enhance-prompt` skill.
   - If the user needs UI generation after design capture, prepare for `stitch-loop` workflows.

## Required Inputs

- Prefer explicit `projectId` and `screenId`.
- If IDs are missing, resolve them from project/screen names before analysis.

## Workflow

1. Discover the Stitch MCP namespace via `list_tools`.
2. Resolve the target project/screen:
   - Call `[prefix]:list_projects` when `projectId` is missing.
   - Call `[prefix]:list_screens` when `screenId` is missing.
3. Fetch source-of-truth artifacts:
   - Call `[prefix]:get_screen` to obtain screenshot URL, HTML URL, dimensions, and device type.
   - Call `[prefix]:get_project` to obtain project metadata and `designTheme`.
   - Download `htmlCode.downloadUrl` (required) and screenshot (recommended) via `web_fetch` or equivalent.
4. Extract observable design facts from HTML + screenshot:
   - Visual atmosphere and density
   - Color tokens (name + hex + role)
   - Typography hierarchy
   - Component styling (buttons, cards/containers, inputs/forms, navigation)
   - Layout and spacing principles
5. Write `DESIGN.md` using `references/design-md-structure.md`.
6. Validate the output before finishing:
   - Every key color includes descriptive name, hex, and functional role.
   - Claims are evidence-based; unknown facts are marked as unknown.
   - Utility-class or CSS details are translated into human-readable design language.
   - No fabricated metrics, product facts, or unsupported behavioral claims.

## Output Rules

- Keep the writing semantic and design-oriented; keep numeric precision in parentheses.
- Separate observed facts from inference when certainty is limited.
- Keep section order and headings stable for prompt reuse.
- Write the final file as `DESIGN.md` in the user's target directory.

## Examples

### Example 1: New Design Document from Screen

**Input:** "Capture the design from my Stitch project 'MobileApp' screen 'Home'."

**Output:**
- Fetches screen HTML and screenshot.
- Extracts color tokens, typography, and component styles.
- Writes `DESIGN.md` with structured sections matching `references/design-md-structure.md`.

### Example 2: Refresh Existing Design Document

**Input:** "Update DESIGN.md with the latest changes from the dashboard screen."

**Output:**
- Reads existing `DESIGN.md` for current structure.
- Fetches updated screen data.
- Merges new observations while preserving existing section order.

## References

- Read `references/design-md-structure.md` for the required section schema and checklist.
- Reuse `examples/DESIGN.md` for tone/format reference only, never as source data.
- Optionally consult the Stitch prompting guide: `https://stitch.withgoogle.com/docs/learn/prompting/`.

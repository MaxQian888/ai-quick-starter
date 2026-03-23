# Documentation Contract

## Root `AGENTS.md`

Use the root `AGENTS.md` as the primary navigation surface.

Required sections:
- repository purpose,
- quick navigation rules,
- module map,
- Mermaid repo diagram,
- high-value module list,
- coverage notes,
- skipped areas,
- recommended next scans.

## Root `CLAUDE.md`

Keep the root `CLAUDE.md` short.

Required behavior:
- act as an alternate discovery entrypoint,
- point back to `AGENTS.md`,
- list the same module docs,
- avoid duplicating the full root narrative.

## Module-Level `CLAUDE.md`

Each selected module doc should include:
- breadcrumbs from repository root,
- what this module is for,
- key files and directories,
- read order,
- Mermaid local structure diagram,
- risks or common misunderstandings,
- nearby modules worth reading next.

## Mermaid Requirement

Each generated root or module doc should contain one Mermaid diagram.

Recommended shapes:
- root docs: repo map or module graph,
- module docs: local folder map or flow of inputs and outputs.

## Coverage Summary

Print this summary in the main conversation after writing docs:

```markdown
## Initialization Summary

### Root Documents
- Status: [created/updated]
- Main sections: <list>

### Identified Modules
- Module count: X
- Modules:
  1. <path>
  2. <path>

### Coverage
- Scanned files: X / Y
- Covered modules: X%
- Skipped reasons: <if any>

### Generated Content
- ✅ Mermaid diagrams
- ✅ Module breadcrumbs

### Recommended Next Scans
- [ ] <path>
```

Adjust the numbers honestly. Estimates are acceptable when exact repo-wide totals would be disproportionately expensive to compute.

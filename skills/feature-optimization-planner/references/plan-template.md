# Optimization Plan Template

Use this template for the final deliverable. Drop sections that are empty, but keep the evidence chain explicit.

```markdown
# <Folder or Feature Name> Optimization Plan

## Executive Summary

<2-3 sentences summarizing the current state, the main risks, and the recommended direction.>

## Audit Scope

- Target repository:
- Target folder:
- Audit goal:
- Verification scope:
- Known blind spots:

## Folder Snapshot

- Source files:
- Test files:
- Config files:
- Documentation files:
- Likely entrypoints:
- Cross-folder dependencies:

## Dependency and Data-Flow Notes

- Entry:
- State or ownership:
- Services or hooks:
- Utilities:
- Types or schemas:
- Tests:
- External integrations:

## Issues By Priority

- HIGH: <count>
- MEDIUM: <count>
- LOW: <count>

### [Priority: HIGH] <Issue Title>

**Location**: `<path/to/file>:<line>`

**Current Problem**:
<Brief description of the issue>

**Suggested Fix**:
<Specific recommendation for improvement>

**Expected Benefit**:
- Performance:
- Maintainability:
- Reliability:

**Effort Estimate**: Small (< 1hr) / Medium (1-4hr) / Large (> 4hr)

**Evidence**:
- <Command result, file read, or external source>

**Assumptions or Blind Spots**:
- <Optional>

### [Priority: MEDIUM] <Issue Title>

**Location**: `<path/to/file>:<line>`

**Current Problem**:
<Brief description of the issue>

**Suggested Fix**:
<Specific recommendation for improvement>

**Expected Benefit**:
- Performance:
- Maintainability:
- Reliability:

**Effort Estimate**: Small (< 1hr) / Medium (1-4hr) / Large (> 4hr)

**Evidence**:
- <Command result, file read, or external source>

### [Priority: LOW] <Issue Title>

**Location**: `<path/to/file>:<line>`

**Current Problem**:
<Brief description of the issue>

**Suggested Fix**:
<Specific recommendation for improvement>

**Expected Benefit**:
- Performance:
- Maintainability:
- Reliability:

**Effort Estimate**: Small (< 1hr) / Medium (1-4hr) / Large (> 4hr)

**Evidence**:
- <Command result, file read, or external source>

## Recommended Action Order

1. <Highest-priority next move>
2. <Second move>
3. <Third move>

## Quick Wins

- <High-impact, low-effort improvement>
- <Another fast follow-up>

## Estimated Total Effort

- Small tasks: <count> (~<hours>)
- Medium tasks: <count> (~<hours>)
- Large tasks: <count> (~<hours>)
- Total: ~<hours>

## Sources

- Local evidence:
  - <files read>
  - <commands run>
- External sources:
  - <official docs / articles / repositories>

## Open Questions

- <Unknown that could change severity or implementation order>
```

## Default output path

When the target repository has a suitable docs surface, prefer:

```text
docs/improvements/<feature-slug>-optimization-plan.md
```

If that path would be noisy or non-standard for the target repository, keep the report inline or use the repository's existing planning directory instead.

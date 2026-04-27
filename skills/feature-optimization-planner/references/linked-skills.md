# Linked Skills

Use this file when the optimization plan is not the final answer and the next step should hand off to a narrower or more execution-focused skill.

## `$build-project-fixer`

Use when:

- the next step is to run real checks and repair failures,
- runtime verification matters more than static reading,
- or the user asks to implement the planned fixes immediately.

## `$feature-gap-requirements-auditor`

Use when:

- the main question is "what documented functionality is still missing?",
- docs, specs, or tickets define the intended feature contract,
- or acceptance criteria need to be extracted from written artifacts first.

## `$project-optimization-opportunity-auditor`

Use when:

- the user wants repository-wide optimization prioritization,
- multiple unrelated subsystems compete for attention,
- or the deliverable should be a broad improvement backlog rather than a single-feature plan.

## `$project-architecture-design-analyzer`

Use when:

- the target feature boundary is still unclear,
- the real entrypoints and ownership seams are not obvious,
- or the repository is unfamiliar enough that an architecture snapshot should happen first.

## `$codebase-indexing-assistant`

Use when:

- the repository is large and a broader reading order is needed,
- the first semantic pass still leaves too many plausible files,
- or the user needs a reusable map of the relevant area before optimization work starts.

## Routing Rule

- Prefer narrower skills once the optimization plan identifies the next exact task.
- Prefer execution-focused skills only after the planning pass has already bounded the work.

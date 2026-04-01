# Input Normalization

Normalize the source before deciding on batches or ownership.

## Supported Input Shapes

### Brief

A short freeform request that already assumes implementation is underway.

Look for verbs such as:

- continue,
- implement,
- fix,
- wire up,
- validate,
- finish,
- or orchestrate.

If the brief is still product-definition work, stop and switch to planning or design.

### Tasks Doc

Usually a structured list of tasks or headings.

Extract:

- stable task titles,
- explicit dependencies,
- verification hints,
- and any noted file or module boundaries.

### Checklist

Treat each checkbox as a candidate work item. Group related checkboxes only when they clearly form one bounded execution unit.

### Spec

Use the spec only to recover execution constraints, not to restart design. Pull out required outputs, non-goals, and any sequencing rules that affect execution.

## Normalization Output

The normalized result should preserve:

- work-item id,
- title,
- source evidence,
- status,
- dependencies,
- write scope,
- verification expectation,
- blocker flag,
- and notes.

If a value is unknown, leave it unknown or record an assumption. Do not invent precision.

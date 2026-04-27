# Context Pack Contract

Always return the final result in this order:

## Successful Patterns

For each selected example, include:

- example name or path,
- why it is relevant to the current task,
- the specific pattern worth copying,
- one boundary or anti-pattern to avoid copying blindly.

## Session Context Pack

Include only what the current session needs next:

- task goal,
- recommended first files to read,
- suggested read order,
- explicit skip zones,
- high-confidence constraints,
- unresolved assumptions,
- stop conditions for further exploration.

Separate:

- `Observed Facts`
- `Inferred Guidance`
- `Unknowns`

## Next Action Guide

State:

- the first concrete action to take,
- whether the helper script needs a narrower rerun,
- when to stop and ask the user,
- what not to do next.

Keep this section operational, not descriptive.

## Helper Evidence Fields

When the helper script is used, treat these fields as ranking evidence:

- `ranking_mode`
- `structure_score`
- `task_score`
- `final_score`
- `matched_terms`
- `why_recommended`

Use them to justify why an example was surfaced. Do not treat them as proof that the example is the only correct choice.

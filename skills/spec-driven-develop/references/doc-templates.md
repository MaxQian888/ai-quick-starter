# Document Templates

Use this file when `docs/progress/` must be repaired manually or when the bootstrap input has not been structured enough for the helper script.

## Phase Input JSON For `bootstrap_progress_docs.py`

The helper script accepts a JSON file shaped like this:

```json
{
  "phases": [
    {
      "name": "Project Analysis",
      "summary": "Map the current architecture and risks.",
      "tasks": [
        "Inventory the main entrypoints",
        { "text": "Record migration risks", "priority": "P0" }
      ],
      "verification": "Analysis reviewed and linked from MASTER.md"
    }
  ]
}
```

## `MASTER.md`

```markdown
# <Task Name> — Progress Tracker

## Task
- Summary: <short task summary>

## References
- [Phase 1: <name>](./phase-1-<name>.md)

## Phase Summary
| Phase | Name | Status | Tasks | Progress |
| --- | --- | --- | --- | --- |
| 1 | <name> | Planned | 0/<n> | Not started |

## Phase Checklist
- [ ] Phase 1: <name> (0/<n> tasks) — [details](./phase-1-<name>.md)

## Current Status
- Current phase: Phase 1 - <name>
- Completed tasks: 0/<total>

## Next Steps
- Start Phase 1.

## Session Log
- [YYYY-MM-DD] Progress docs initialized.
```

## `phase-N-<name>.md`

```markdown
# Phase N: <Phase Name>

## Purpose
<why this phase exists>

## Tasks
- [ ] TN.1 [P1] <task one>
- [ ] TN.2 [P0] <task two>

## Dependencies
- Depends on: None

## Verification
- Verification boundary: <expected evidence>

## Notes
- Add blockers, clarifications, or handoff notes here.

## Phase Completion Checklist
- [ ] All phase tasks completed
- [ ] Relevant verification run or marked blocked
- [ ] MASTER.md phase count updated
- [ ] MASTER.md current status advanced
```

## Sub-Skill Template

Use this section when Phase 4 needs a concrete child-skill outline or when the generated child skill has drifted away from the intended handoff contract.

When creating a task-specific child skill, keep the payload small and project-specific. Provide the skill creator with:

- **Name**: `<task-type>-dev` or another short project-specific execution name
- **Description**: trigger language tied to the actual migration, rewrite, or execution phase
- **Content outline**:
  1. Cross-conversation continuity protocol
  2. Project-specific execution scope
  3. Progress update instructions
  4. Verification-boundary rules
  5. Parallel Execution Protocol
  6. Cleanup trigger

### Parallel Execution Protocol

The generated child skill should include a section like this:

```markdown
## Parallel Execution

At the start of each development session:

1. Read `docs/progress/MASTER.md` first and locate the active phase file.
2. Read the current phase's lane or checkpoint notes before parallelizing.
3. If the phase has multiple safe lanes:
   - Launch one executor per lane only when write scopes are disjoint.
   - Keep blocker resolution, merge decisions, and `MASTER.md` reconciliation on the main thread.
4. If the phase has one lane or the merge risk is high, execute sequentially.
5. After lane work returns:
   - Update the phase file immediately.
   - Reconcile `MASTER.md` on the main thread.
   - Run the required verification before calling the checkpoint complete.
```

## Sample Child Skill Fixture

Use `assets/examples/sample-child-skill/` as the reference example when you need a concrete fixture for the expected child-skill shape.

## Sample Progress Fixture

Use `assets/examples/sample-progress/docs/progress/` as the reference resume fixture when you need a stable example of `MASTER.md` plus linked phase files for end-to-end handoff testing.

## Sample Bootstrap Fixture

Use `assets/examples/sample-bootstrap/` when you need a round-trip example that binds `phases.json`, the bootstrap helper, and the expected initial `docs/progress/` output together.

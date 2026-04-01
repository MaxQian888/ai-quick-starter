# Execution Workflow

Use this workflow when the request already has planning context and now needs execution orchestration.

## Step 1: Normalize The Source

Read the input and extract:

- work items,
- dependency edges,
- write scopes,
- merge points,
- blockers,
- and verification expectations.

If a statement is ambiguous, preserve it as an assumption instead of inventing certainty.

## Step 2: Separate Main Thread From Delegated Work

Keep these on the main thread:

- blockers on the critical path,
- tasks that cut across multiple write scopes,
- checkpoint review,
- integration,
- and final verification.

Delegate only bounded work whose scope and return condition are clear.

## Step 3: Build Execution Waves

Group independent work into waves. Each wave should state:

- objective,
- work-item ids,
- owners,
- allowed write scopes,
- return condition,
- and next checkpoint id.

Avoid building waves that depend on speculative future edits.

## Step 4: Run And Collect

Treat each wave as provisional until the checkpoint review finishes. Returned work is evidence, not an automatic merge.

## Step 5: Checkpoint Review

At the checkpoint, confirm:

1. what completed,
2. what drifted out of scope,
3. what verification ran,
4. what blockers remain,
5. and whether the next wave still has valid assumptions.

## Step 6: Re-Plan Or Close

If assumptions changed, rebuild the remaining waves. If the remaining scope is exhausted and verification ran, summarize verified completion and any unverified edges.

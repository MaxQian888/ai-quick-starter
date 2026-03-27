# Safe Command Patterns

Use these patterns to turn risky intent into reviewable command sequences.

## List-First

Show the candidate targets before any side effect.

Use for:

- deletes,
- moves,
- bulk rename,
- batch edits.

## Preview-Then-Act

Split the response into:

1. `Pre-check`
2. `Preview`
3. `Execute`
4. `Verify`

Use for:

- recursive deletes,
- overwrite operations,
- process termination,
- environment mutation,
- bulk replacements.

## Filter-Then-Act

Constrain the target set by exact identifier, extension, known directory, or explicit file list before acting.

Bad shape:

- broad wildcard first,
- recursion first,
- force flag first.

Better shape:

- enumerate,
- filter,
- review,
- then mutate.

## Verify-After

Always provide the command that proves the result, especially after state changes.

Examples:

- delete -> rerun the listing command and show no remaining matches,
- copy -> show destination file metadata or checksum,
- replace -> rerun the search and show the new state,
- PATH edit -> print the old and new value explicitly.

## Common Operation Shapes

### Delete

- `Pre-check`: confirm the parent path exists
- `Preview`: list the exact files or directories that match
- `Execute`: remove only the reviewed target set
- `Verify`: rerun the listing and confirm zero matches

### Replace

- `Pre-check`: find candidate files
- `Preview`: show the current matches or diff
- `Execute`: apply the replacement to the constrained set
- `Verify`: rerun the search and confirm the old pattern is gone

### Copy Or Move

- `Pre-check`: confirm source and destination parent path
- `Preview`: show the resolved source and destination
- `Execute`: perform the copy or move
- `Verify`: inspect the destination file

### Process Termination

- `Pre-check`: list matching processes with IDs
- `Preview`: show the exact process IDs that would be terminated
- `Execute`: terminate only the reviewed IDs
- `Verify`: query the process list again

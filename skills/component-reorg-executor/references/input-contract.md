# Input Contract

This skill consumes the JSON output of `component-reorg-planner`.

## Required Top-Level Fields

- `root`
- `target_directory`
- `move_plan`

## Required Move Entry Fields

- `path`
- `action`
- `destination_path`
- `proposed_subfolder`

## Accepted Actions

- `move`: execute the file move
- `keep-put`: record as skipped and leave untouched

## Reject Or Stop When

- `root` does not match the current repository
- a `move` source file no longer exists
- a destination path now conflicts with an unexpected file
- the move graph was generated for a different target directory
- the plan needs new buckets or new file classifications, because that means the planner is stale

# Dangerous Command Catalog

Use this file whenever the request touches a broad or destructive command family.

## Recursive Delete

High-risk examples:

- `rm -rf ...`
- `Remove-Item -Recurse -Force ...`

Why risky:

- recursion and force flags magnify path mistakes,
- globs or mistaken working directories can widen the blast radius,
- deletes are often hard to recover.

Safer shape:

- list matching directories first,
- review the exact resolved paths,
- delete only the reviewed list,
- verify nothing remains.

## Overwrite Redirection

High-risk examples:

- `> file`
- `Out-File -Force`

Why risky:

- silently truncates or replaces existing content,
- easy to target the wrong file during path mistakes.

Safer shape:

- inspect the destination first,
- back up when appropriate,
- then write the new content,
- verify file size, timestamp, or diff.

## `git clean -fdx`

Why risky:

- removes untracked and ignored files,
- often destroys local caches, generated files, and scratch work.

Safer shape:

- run `git status --short --ignored`,
- preview with `git clean -fdxn`,
- then execute only if the preview matches intent.

## PATH Or Environment Mutation

Why risky:

- can break command resolution,
- can persist across sessions or users,
- easy to introduce malformed separators or duplicate entries.

Safer shape:

- print the current value,
- print the proposed new value,
- apply the change,
- print the final value again.

## Process Tree Termination

Why risky:

- broad name matching can kill unrelated workloads,
- child-process trees may belong to other tasks.

Safer shape:

- list processes with IDs and command lines,
- review exact PIDs,
- terminate only the reviewed PIDs,
- verify the process list after termination.

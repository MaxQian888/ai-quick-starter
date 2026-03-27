# Risk Triage

Use this file to classify the request before writing commands.

## `low`

Use for read-only or observational work with no meaningful side effects.

Common examples:

- list files,
- inspect logs,
- show environment variables,
- show git status,
- query running processes.

Minimum response shape:

- `Shell`
- `Risk`
- `Execute`
- `Notes` only when shell syntax could surprise the user

## `medium`

Use for narrow state changes with a clear target and limited blast radius.

Common examples:

- create one directory,
- copy or move one known file,
- update one config file,
- install a dependency in one known project,
- rename a reviewed set of files.

Minimum response shape:

- `Shell`
- `Risk`
- `Pre-check`
- `Execute`
- `Verify`
- `Notes`

Do not skip the pre-check. Confirm the target exists and matches the user's intent before mutation.

## `high`

Use for destructive, recursive, batch, overwrite, permission, or system-impacting work.

Common examples:

- recursive delete,
- force overwrite,
- bulk replace,
- `git clean -fdx`,
- modify `PATH`,
- kill process trees,
- download then execute.

Minimum response shape:

- `Shell`
- `Risk`
- `Pre-check`
- `Preview`
- `Execute`
- `Verify`
- `Notes`

Rules:

- Do not start with the destructive command.
- Show the affected targets before mutation.
- Prefer a safer alternative when one exists.

## `blocked`

Use when the request is too ambiguous, clearly malicious, or too dangerous to answer with an execution command.

Common examples:

- "wipe whatever is causing the problem",
- "delete everything related to build issues",
- requests that bypass safety controls,
- destructive work against a vague path or broad machine scope.

Minimum response shape:

- `Shell` only if a read-only discovery shell is still relevant
- `Risk`
- read-only discovery commands
- a short explanation of what information is missing

Rules:

- Do not provide the execution command.
- Ask the user to narrow the target, or provide commands that only discover the boundary.

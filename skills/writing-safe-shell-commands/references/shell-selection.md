# Shell Selection

Choose the shell before writing the command sequence.

## Default Rules

- Keep the user's requested shell unless it would make the command less safe or less clear.
- Prefer PowerShell for Windows filesystem, environment, and process-management tasks.
- Prefer `cmd` only when the request explicitly targets batch compatibility, `%VAR%` syntax, or Windows `cmd.exe` behavior.
- Prefer `bash` when the task clearly targets POSIX tooling, shell scripts, or a Unix-like environment.

## Shell Pitfalls

### PowerShell

- Single quotes do not expand variables.
- Use `-LiteralPath` for user-supplied filesystem paths when wildcard expansion would be unsafe.
- `Get-ChildItem`, `Copy-Item`, and `Remove-Item` behave differently from Unix tools; be explicit about recursion and force flags.

### `cmd`

- `%VAR%` expansion is not the same as PowerShell or bash.
- Quoting and escaping are brittle around `^`, `%`, and delayed expansion.
- Avoid `cmd` for complex filtering or path-heavy destructive work unless the user explicitly requires it.

### `bash`

- Globs expand before the command runs unless quoted.
- `'single quotes'` and `"double quotes"` behave differently for variable expansion.
- Paths with spaces need strict quoting or array-safe handling.

## When To Recommend A Different Shell

Switch shells only when it materially improves safety or clarity.

Examples:

- User asks for a Windows filesystem cleanup "in any shell" -> prefer PowerShell.
- User asks to modify a `.bat` pipeline -> keep `cmd`.
- User asks to operate inside an existing bash deployment script -> keep `bash`.

If you switch, say why in the `Shell` section instead of silently changing syntax families.

# Language Patterns

Read this file before editing comments in mixed-language repositories.

## TypeScript, JavaScript, TSX, JSX

- Prefer short inline comments near the exact branch, condition, or transform that needs explanation.
- Keep component comments focused on rendering constraints, state coupling, or framework quirks.
- Do not add comments to obvious prop destructuring, imports, or trivial event handlers.
- In TSX or JSX, comment only when layout or render behavior is non-obvious.

## Python

- Preserve module, class, or function docstrings when the local area already uses them.
- Use inline comments for local hazards or decisions that do not belong in a docstring.
- Do not replace a concise, useful docstring with a paragraph of tutorial prose.
- If the module is docstring-light, prefer a few inline comments over inventing docstrings everywhere.

## Shell

- Comment dangerous quoting, path, or subshell behavior.
- Keep comments short because long prose is hard to scan in scripts.
- Do not narrate basic variable assignment or command sequencing.
- Prefer comments that explain why a safer shell pattern is required.

## PowerShell

- Comment only the non-obvious parts: `-LiteralPath`, wildcard hazards, object-shape assumptions, or `ShouldProcess` behavior.
- Reuse local verb and noun choices instead of translating everything into generic admin language.
- Do not explain standard cmdlets unless the local usage is unusual.

## Mixed-Language Rule

- Treat each language surface separately.
- Do not force Python docstring habits onto TypeScript.
- Do not force TS-style inline comments onto PowerShell scripts that already rely on brief header notes.
- When one directory mixes styles, sample the nearest same-language files before editing.

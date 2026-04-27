# Component Ecosystem

## First Choice: Official Component Suite

Use `@inkjs/ui` first for common interactive controls.
Repository: https://github.com/vadimdemedes/ink-ui

Typical components include:

- `TextInput`
- `Select`
- `MultiSelect`
- `Spinner`
- `ProgressBar`
- `Alert`
- `StatusMessage`
- `Table`
- `Header`
- `Badge`
- `PasswordInput`

Prefer this package before collecting many unrelated third-party components.

## Common Third-Party Packages (Use Selectively)

- `ink-spinner`
- `ink-text-input`
- `ink-select-input`
- `ink-table`
- `ink-link`
- `ink-gradient`
- `ink-big-text`
- `ink-task-list`
- `ink-markdown`

## Selection Rules

1. Prefer maintained packages with recent releases and clear Node/React compatibility.
2. Keep dependency count low; avoid mixing multiple packages that solve the same problem.
3. Validate keyboard/focus behavior after adding any third-party component.
4. Add a regression test for every new external component integration.

## Integration Checklist

- Dependency is compatible with Ink v6 + React 19.
- Focus and keyboard interaction works with your app's `useInput` flow.
- Non-interactive mode does not break output formatting.
- CI includes at least one test that renders the new component path.

## Practical Recommendation

For greenfield projects, start with:

1. Core Ink primitives (`Box`, `Text`, hooks)
2. `@inkjs/ui` for advanced controls
3. Additional third-party packages only for missing capabilities

# Built-In Libraries

## Canonical Names And Aliases

| Canonical name | Common aliases |
| --- | --- |
| `shadcn/ui` | `shadcn`, `shadcn-ui` |
| `mui` | `MUI`, `@mui/material`, `material-ui` |
| `ant-design` | `antd`, `Ant Design`, `ant design` |
| `chakra-ui` | `chakra`, `@chakra-ui/react`, `Chakra UI` |
| `heroui` | `HeroUI`, `hero ui`, `@heroui/react` |

## First-Pass Mapping Coverage

The audit only treats these categories as low-ambiguity automatic candidates in version one:

- `button` -> `Button`
- `input` -> `Input`
- `textarea` -> `Textarea`
- `select` -> `Select`

These categories may appear in the report but should usually stay blocked or manual unless the repository already uses the exact target library pattern:

- dialog or modal
- drawer
- tabs
- checkbox, radio, switch with custom state wiring
- table-like or grid-like views

## Safety Notes By Library

### `shadcn/ui`

- Safe only when the repository already tolerates local component imports and wrapper-based composition.
- Be conservative around Radix-driven overlays and form primitives.

### `mui`

- Safe for obvious `Button` and `Input`-style replacements.
- Be conservative around theme usage, slot props, and composite widgets.

### `ant-design`

- Safe for low-ambiguity form primitives.
- Be conservative around modal, table, and validation-heavy form usage.

### `chakra-ui`

- Safe for simple primitives when the file is not already wrapped by a local design-system layer.
- Be conservative around responsive prop systems and composed overlays.

### `heroui`

- Safe for simple primitives only.
- Be conservative around overlays, data-heavy widgets, and custom tokens.

## Unsupported Libraries

Unsupported target libraries stay in audit-only mode in version one:

- report candidate categories,
- explain likely migration seams,
- keep `safe_fix_plan` empty,
- do not emit direct replacement edits.

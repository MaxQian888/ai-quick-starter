# Grouping Rules

The planner groups files only when the filename exposes a strong functional signal.

## Supported Functional Buckets

- `forms`: `Form`, `Field`, `Input`, `Select`, `Checkbox`, `Radio`, `Switch`, `Picker`, `Editor`
- `data-display`: `Table`, `Grid`, `List`, `Row`, `Column`
- `overlays`: `Dialog`, `Modal`, `Drawer`, `Sheet`, `Popover`, `Tooltip`
- `navigation`: `Tabs`, `Nav`, `Menu`, `Breadcrumb`, `Pagination`, `Stepper`
- `filters`: `Filter`, `Filters`, `Search`, `Query`, `Sort`, `Facet`
- `feedback`: `Alert`, `Toast`, `Error`, `Empty`, `Loading`, `Skeleton`, `Success`
- `analytics`: `Chart`, `Graph`, `Metric`, `Stats`, `Sparkline`

## Keep-Put Rules

Keep these files in place by default:

- hooks such as `useX.ts`
- barrel files such as `index.ts`
- tests and stories
- styles and CSS modules
- type-only files
- components whose names do not expose a clear bucket

## Conservative Bias

- Do not move `Card`, `Panel`, or other generic names without stronger local evidence.
- Do not create a generic `shared` bucket to make the output look complete.
- Prefer fewer move candidates with explicit rationale over broad folder churn.

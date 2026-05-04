---
name: shadcn-component-migrator
description: >
  Migrate custom React components to shadcn/ui equivalents in Next.js/TypeScript projects.
  Use this skill when the user asks to replace custom components with shadcn/ui components,
  audit components for shadcn/ui migration, refactor UI components to use shadcn/ui,
  or mentions "shadcn" + "component" + "replace/migrate/audit/refactor" in any combination.
  Also trigger when the user wants to standardize component usage, eliminate custom UI primitives,
  or modernize components to match the design system. Works with any folder containing .tsx components.
  Prioritize single shadcn/ui component replacements; skip composite components built from multiple shadcn pieces.
  Preserve responsive Tailwind classes and ensure layout compatibility.
---

# shadcn/ui Component Migrator

Migrate custom React components to their shadcn/ui equivalents.

## Core Rules

1. **Single-component replacement only**: Only replace a custom component if it maps to a single shadcn/ui primitive. Skip components that are already composed of 2+ shadcn/ui imports or complex business logic.
2. **Preserve the public API**: Keep the original component's props interface unchanged. Consumers should not need to update call sites.
3. **Responsive behavior must survive**: Audit and preserve all responsive Tailwind classes (`sm:`, `md:`, `lg:`, `xl:`, `2xl:`) from the original component.
4. **Direct file modification**: After confirming the migration is correct, write the new code directly to the original file.
5. **Use MCP for uncertain mappings**: When unsure which shadcn/ui component to use, call the shadcn MCP tools to view component docs and examples.

## Workflow

### Step 1: Scan Target Folder

List all `.tsx` files in the user-specified folder. Exclude:
- Files ending in `.test.tsx`
- Files inside `components/ui/` (already shadcn/ui)
- Files with zero JSX output (pure logic/hooks)

For each file, read its contents to build a candidate list.

### Step 2: Filter Candidates

Skip a component if ANY of the following are true:
- It imports 2 or more components from `@/components/ui/*` (already using multiple shadcn/ui primitives)
- It contains 3+ React hooks (`useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`, etc.)
- It contains internal state or async data fetching
- It is longer than 80 lines AND has complex conditional rendering trees
- It is a layout/page component rather than a reusable UI primitive
- It renders a data table, chart, canvas, or editor (too specialized)

Mark remaining files as **migration candidates**.

### Step 3: Map to shadcn/ui Component

For each candidate, determine the matching shadcn/ui component by analyzing:

**Component name patterns:**
| Name contains | Likely shadcn/ui match |
|---------------|------------------------|
- `Button`, `Btn` | `Button` |
- `Badge`, `Tag`, `Pill`, `Label` (display) | `Badge` |
- `Alert`, `Banner`, `Toast`, `Notice`, `Message` | `Alert` or `Sonner` |
- `Input`, `Field`, `TextField` | `Input` |
- `TextArea`, `Textarea` | `Textarea` |
- `Select`, `Dropdown`, `Picker` | `Select` |
- `Checkbox`, `Check` | `Checkbox` |
- `Radio`, `Option` | `RadioGroup` |
- `Switch`, `Toggle` (single) | `Switch` |
- `Dialog`, `Modal`, `Drawer` | `Dialog` or `Sheet` or `Drawer` |
- `Tooltip`, `Hint` | `Tooltip` |
- `Popover`, `Popup` | `Popover` |
- `Card`, `Panel`, `Tile` | `Card` |
- `Skeleton`, `Loading`, `Placeholder`, `Shimmer` | `Skeleton` |
- `Progress`, `Bar`, `Meter` | `Progress` |
- `Separator`, `Divider`, `Line` | `Separator` |
- `Avatar`, `ProfilePic` | `Avatar` |
- `Accordion`, `Collapse`, `Expand` | `Accordion` |
- `Tabs`, `Tab` | `Tabs` |
- `Menu`, `Nav` | `NavigationMenu` or `Menubar` |
- `Table`, `Grid` (data) | `Table` |
- `Calendar`, `DatePicker` | `Calendar` |
- `Command`, `CommandPalette`, `Search` | `Command` |
- `ContextMenu`, `RightClick` | `ContextMenu` |
| `Slider`, `Range` | `Slider` |
| `ScrollArea`, `Scroller` | `ScrollArea` |
| `HoverCard` | `HoverCard` |
| `Carousel`, `Slider` (image) | `Carousel` |
| `Collapsible` | `Collapsible` |

**DOM structure patterns:**
- `<button>` or clickable element → `Button`
- `<input type="text">` or `<input>` → `Input`
- `<select>` → `Select`
- `<textarea>` → `Textarea`
- `<input type="checkbox">` → `Checkbox`
- `<input type="radio">` → `RadioGroup`
- `<table>` → `Table`
- `<hr>` or visual divider → `Separator`
- `<img>` for avatar/profile → `Avatar`
- `<dialog>` or overlay → `Dialog`/`Sheet`
- `<a>` styled as button → `Button` with `asChild` or `LinkButton`

**Props patterns:**
- `variant` + `size` + optional `onClick` → `Button`
- `variant` + `children` text → `Badge` or `Alert`
- `message` + optional `onRetry`/`onDismiss` → `Alert`
- `value` + `onChange` + `placeholder` → `Input` or `Textarea`
- `checked` + `onCheckedChange` → `Switch` or `Checkbox`
- `open` + `onOpenChange` → `Dialog`, `Sheet`, `Popover`, or `DropdownMenu`

If uncertain after name/DOM/props analysis, call the shadcn MCP:
```
mcp__shadcn__search_items_in_registries with query="<description of what the component does>"
```
Then view matching components:
```
mcp__shadcn__view_items_in_registries with items=["@shadcn/<component-name>"]
```

### Step 4: Verify shadcn/ui Component Exists in Project

Before migrating, confirm the target shadcn/ui component exists in the project's `components/ui/` directory. If it does not exist:
1. Check if it can be added via the shadcn CLI:
   ```bash
   pnpm dlx shadcn@latest add <component-name>
   ```
2. If the CLI install is not possible or fails, skip this component and note it in the report.

### Step 5: Generate Replacement Code

When replacing, follow these code patterns:

**Preserve the original props interface**: Do not change the exported type/interface. Internal implementation may change, but external callers must work unchanged.

**Import style**:
```tsx
import { <Component> } from "@/components/ui/<component-kebab-case>"
```

**ClassName merging**: Always use `cn()` from `@/lib/utils` to merge shadcn/ui default classes with any `className` prop passed by consumers.

**Responsive class preservation**: Before modifying, extract all responsive Tailwind classes from the original component. Ensure they are preserved in the new implementation:
- Classes like `md:flex-row`, `lg:w-64`, `sm:px-2`, `max-md:hidden` must survive
- If the shadcn/ui component wraps the original structure differently, apply the responsive classes to the outermost exported element or the shadcn component's `className`

**Common migration patterns:**

```tsx
// Before: Custom error banner
export function ErrorBanner({ message, onRetry, className }: { message: string; onRetry?: () => void; className?: string }) {
  return (
    <div className={cn("flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3", className)}>
      <AlertCircle className="size-4 shrink-0 text-red-600" />
      <span className="flex-1 text-sm text-red-800">{message}</span>
      {onRetry && <button onClick={onRetry}>Retry</button>}
    </div>
  );
}

// After: Using shadcn/ui Alert
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function ErrorBanner({ message, onRetry, className }: { message: string; onRetry?: () => void; className?: string }) {
  return (
    <Alert variant="destructive" className={cn(className)}>
      <AlertCircle className="size-4" />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription className="flex items-center gap-2">
        {message}
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            Retry
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}
```

Wait — the above example uses Alert + Button, which is 2 shadcn/ui components. This violates the single-component rule. Do NOT do this. Instead, if the original has action buttons inside, either:
- Keep the action button as a plain `<button>` if it's simple, OR
- Skip migration if the component inherently needs multiple primitives

**Correct approach for simple replacements:**

```tsx
// Before: Simple status badge
export function StatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", className)}>
      {status}
    </span>
  );
}

// After: Using shadcn/ui Badge
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <Badge variant="secondary" className={cn(className)}>
      {status}
    </Badge>
  );
}
```

### Step 6: Responsive Audit Checklist

Before writing the file, verify:
- [ ] All original responsive classes (`sm:`, `md:`, `lg:`, `xl:`, `max-sm:`, etc.) are present
- [ ] The shadcn/ui component does not impose conflicting fixed dimensions
- [ ] Container queries or flex/grid parents still behave correctly
- [ ] Mobile-first ordering is preserved (`order-`, `flex-col md:flex-row`, etc.)
- [ ] Hidden/show logic at breakpoints is unchanged (`hidden md:block`, `md:hidden`, etc.)

If the shadcn/ui component has a different internal structure that would break the responsive behavior (e.g., it adds a wrapper div that interferes with flex/grid layout), either:
- Apply responsive classes to the shadcn component's `className` prop
- Or skip migration with a note

### Step 7: Write and Report

For each migrated component:
1. Write the new code to the original file path using the Write or Edit tool
2. Add a brief summary to the migration report

Report format:
```
## Migration Report: <folder-name>

### Migrated (<count>)
| File | Original Pattern | shadcn/ui Component | Notes |
|------|-----------------|---------------------|-------|
| `components/shared/error-banner.tsx` | Custom div alert | `Alert` | Preserved `className` and `onRetry` |

### Skipped (<count>)
| File | Reason |
|------|--------|
| `components/agent/agent-card.tsx` | Already uses 3 shadcn/ui components (Card, Badge, Progress) |
| `components/agents/agent-sidebar-item.tsx` | Complex component with multiple hooks and shadcn/ui imports |

### Not Found (<count>)
| File | Missing shadcn/ui Component |
|------|---------------------------|
| `components/shared/foo.tsx` | `Slider` not in components/ui/ |
```

## Important Notes

- **Never** replace a component if it would require consumers to change their import paths or prop names.
- **Never** replace a component that renders third-party widgets (editors, charts, maps, calendars from libraries like `react-calendar`).
- **Never** add new shadcn/ui component files to `components/ui/` yourself — use the shadcn CLI (`pnpm dlx shadcn@latest add <name>`) or skip.
- **Always** check that the migrated component still compiles by looking for TypeScript errors after the change.
- When a component is borderline (could be replaced but loses some minor styling), prefer **keeping the original** to avoid regressions.
- The shadcn/ui components in this project use Tailwind v4 with oklch colors and the `new-york` style variant.

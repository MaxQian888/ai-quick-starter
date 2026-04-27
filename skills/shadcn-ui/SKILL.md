---
name: shadcn-ui
description: >
  Use this skill whenever you need to add, customize, integrate, or troubleshoot shadcn/ui components in a React or Next.js project.
  Make sure to use it when the user wants to install UI components, set up a new shadcn/ui project, customize themes and variants, build forms or dialogs, or explore the component registry and blocks catalog.
  Covers component discovery via MCP tools, CLI installation, Tailwind theming, Radix UI and Base UI primitives, custom registries, and accessibility best practices.
---

# shadcn/ui Component Integration

Discover, install, and customize shadcn/ui components while preserving accessibility and theming standards.

## Adaptive Detection

Before adding components, scan for:
- `package.json` to confirm React (18+) and Next.js (13+) versions if applicable
- `components.json` to detect existing shadcn/ui configuration
- `tailwind.config.*` and `app/globals.css` for theme setup
- `lib/utils.ts` or equivalent for the `cn()` utility
- `tsconfig.json` for `@/*` path aliases
- Existing component library conflicts (Material-UI, Chakra, etc.)

## Core Principles

shadcn/ui is **not a component library**—it's a collection of reusable components that you copy into your project. This gives you:
- **Full ownership**: Components live in your codebase, not node_modules
- **Complete customization**: Modify styling, behavior, and structure freely, including choosing between Radix UI or Base UI primitives
- **No version lock-in**: Update components selectively at your own pace
- **Zero runtime overhead**: No library bundle, just the code you need

## Component Discovery and Installation

### 1. Browse Available Components

Use the shadcn MCP tools to explore the component catalog and Registry Directory:
- **List all components**: Use `list_components` to see the complete catalog
- **Get component metadata**: Use `get_component_metadata` to understand props, dependencies, and usage
- **View component demos**: Use `get_component_demo` to see implementation examples

### 2. Component Installation

There are two approaches to adding components:

**A. Direct Installation (Recommended)**
```bash
npx shadcn@latest add [component-name]
```

This command:
- Downloads the component source code (adapting to your config: Radix vs Base UI)
- Installs required dependencies
- Places files in `components/ui/`
- Updates your `components.json` config

**B. Manual Integration**
1. Use `get_component` to retrieve the source code
2. Create the file in `components/ui/[component-name].tsx`
3. Install peer dependencies manually
4. Adjust imports if needed

### 3. Registry and Custom Registries

If working with a custom registry (defined in `components.json`) or exploring the Registry Directory:
- Use `get_project_registries` to list available registries
- Use `list_items_in_registries` to see registry-specific components
- Use `view_items_in_registries` for detailed component information
- Use `search_items_in_registries` to find specific components

## Project Setup

### Initial Configuration

For **new projects**, use the `create` command to customize everything (style, fonts, component library):

```bash
npx shadcn@latest create
```

For **existing projects**, initialize configuration:

```bash
npx shadcn@latest init
```

This creates `components.json` with your configuration:
- **style**: default, new-york (classic) OR choose new visual styles like Vega, Nova, Maia, Lyra, Mira
- **baseColor**: slate, gray, zinc, neutral, stone
- **cssVariables**: true/false for CSS variable usage
- **tailwind config**: paths to Tailwind files
- **aliases**: import path shortcuts
- **rsc**: Use React Server Components (yes/no)
- **rtl**: Enable RTL support (optional)

### Required Dependencies

shadcn/ui components require:
- **React** (18+)
- **Tailwind CSS** (3.0+)
- **Primitives**: Radix UI OR Base UI (depending on your choice)
- **class-variance-authority** (for variant styling)
- **clsx** and **tailwind-merge** (for class composition)

### Setup Verification

Before adding a large component set, validate local project wiring:

- Python: `python scripts/verify-setup.py`
- Bash: `bash scripts/verify-setup.sh`
- PowerShell: `./scripts/verify-setup.ps1`

Fix blocking findings first (missing `components.json`, missing Tailwind config, or missing `lib/utils.ts`) before component installation.

## Component Architecture

### File Structure
```
src/
├── components/
│   ├── ui/              # shadcn components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── dialog.tsx
│   └── [custom]/        # your composed components
│       └── user-card.tsx
├── lib/
│   └── utils.ts         # cn() utility
└── app/
    └── page.tsx
```

### The `cn()` Utility

All shadcn components use the `cn()` helper for class merging:

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

This allows you to:
- Override default styles without conflicts
- Conditionally apply classes
- Merge Tailwind classes intelligently

## Customization Best Practices

### 1. Theme Customization

Edit your Tailwind config and CSS variables in `app/globals.css`:

```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    /* ... more variables */
  }
  
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark mode overrides */
  }
}
```

### 2. Component Variants

Use `class-variance-authority` (cva) for variant logic:

```typescript
import { cva } from "class-variance-authority"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        outline: "border border-input",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)
```

### 3. Extending Components

Create wrapper components in `components/` (not `components/ui/`):

```typescript
// components/custom-button.tsx
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"

export function LoadingButton({ 
  loading, 
  children, 
  ...props 
}: ButtonProps & { loading?: boolean }) {
  return (
    <Button disabled={loading} {...props}>
      {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {children}
    </Button>
  )
}
```

## Blocks and Complex Components

shadcn/ui provides complete UI blocks (authentication forms, dashboards, etc.):

1. **List available blocks**: Use `list_blocks` with optional category filter
2. **Get block source**: Use `get_block` with the block name
3. **Install blocks**: Many blocks include multiple component files

Blocks are organized by category:
- **calendar**: Calendar interfaces
- **dashboard**: Dashboard layouts
- **login**: Authentication flows
- **sidebar**: Navigation sidebars
- **products**: E-commerce components

## Accessibility

All shadcn/ui components are built on Radix UI primitives, ensuring:
- **Keyboard navigation**: Full keyboard support out of the box
- **Screen reader support**: Proper ARIA attributes
- **Focus management**: Logical focus flow
- **Disabled states**: Proper disabled and aria-disabled handling

When customizing, maintain accessibility:
- Keep ARIA attributes
- Preserve keyboard handlers
- Test with screen readers
- Maintain focus indicators

## Common Patterns

### Form Building
```typescript
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

// Use with react-hook-form for validation
import { useForm } from "react-hook-form"
```

### Dialog/Modal Patterns
```typescript
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
```

### Data Display
```typescript
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
```

## Troubleshooting

### Import Errors
- Check `components.json` for correct alias configuration
- Verify `tsconfig.json` includes the `@` path alias:
  ```json
  {
    "compilerOptions": {
      "paths": {
        "@/*": ["./src/*"]
      }
    }
  }
  ```

### Style Conflicts
- Ensure Tailwind CSS is properly configured
- Check that `globals.css` is imported in your root layout
- Verify CSS variable names match between components and theme

### Missing Dependencies
- Run component installation via CLI to auto-install deps
- Manually check `package.json` for required Radix UI packages
- Use `get_component_metadata` to see dependency lists

### Version Compatibility
- shadcn/ui v4 requires React 18+ and Next.js 13+ (if using Next.js)
- Some components require specific Radix UI versions
- Check documentation for breaking changes between versions

## Validation and Quality

Before committing components:
1. **Type check**: Run `tsc --noEmit` to verify TypeScript
2. **Lint**: Run your linter to catch style issues
3. **Test accessibility**: Use tools like axe DevTools
4. **Visual QA**: Test in light and dark modes
5. **Responsive check**: Verify behavior at different breakpoints

## Resources

Refer to the following resource files for detailed guidance:
- `resources/setup-guide.md` - Step-by-step project initialization
- `resources/component-catalog.md` - Complete component reference
- `resources/customization-guide.md` - Theming and variant patterns
- `resources/migration-guide.md` - Upgrading from other UI libraries

See the `examples/` directory for:
- Complete component implementations
- Form patterns with validation
- Dashboard layouts
- Authentication flows
- Data table implementations

## Examples

**Example 1: Add a dialog to an existing project**
```
User: "I need a dialog component in my Next.js app."
Agent: Verify setup with `scripts/verify-setup.sh`, run `npx shadcn@latest add dialog`, ensure imports use the `@/` alias, and provide a usage example with DialogTrigger and DialogContent.
```

**Example 2: Customize the primary color theme**
```
User: "Change the primary color to emerald across the whole app."
Agent: Edit CSS variables in `app/globals.css` for both `:root` and `.dark` modes, update `--primary` to emerald HSL values, and verify the change renders in light and dark modes.
```

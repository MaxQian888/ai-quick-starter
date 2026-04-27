# Grader

## Purpose

Evaluate whether the agent correctly discovered components, verified project setup, installed components safely, and maintained accessibility and theming standards.

## Scoring Criteria

1. **Setup Verification** (25%): Was the project verified for `components.json`, Tailwind config, and `lib/utils.ts` before adding components?
2. **Discovery** (20%): Were MCP tools or CLI used to discover components rather than guessing?
3. **Installation** (20%): Was `npx shadcn@latest add` preferred over manual integration?
4. **Customization** (15%): Were wrapper components created in `components/` rather than editing `components/ui/`?
5. **Accessibility** (20%): Were ARIA attributes, keyboard handlers, and focus indicators preserved?

## Pass Threshold

Score >= 75% to pass.

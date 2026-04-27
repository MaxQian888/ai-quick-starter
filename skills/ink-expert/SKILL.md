---
name: ink-expert
description: |
  Use this skill whenever you are building, migrating, or troubleshooting Ink CLI applications.
  Make sure to use this skill whenever the user mentions Ink v6, React 19 terminal apps, Ink migration,
  interactive terminal UX, usePaste, useBoxMetrics, useCursor, useFocusManager, ink-testing-library,
  or debugging Ink rendering issues. Also trigger for requests like "migrate my Ink app",
  "upgrade Ink to latest", "fix my Ink layout", "add paste support to my CLI", "make my Ink tests pass in CI",
  or "what's the best Ink component for tables/forms". Covers production-grade patterns, version-aware
  migration steps, and the full Ink v6 + React 19 API surface.
---

# Ink Expert

Build and troubleshoot production-grade Ink CLIs with current APIs and version-aware migration steps.
Treat this skill as the default path when a task includes Ink architecture, interactive terminal UX, or Ink testing.

## Adaptive Detection

Before writing or changing Ink code, detect the runtime baseline:

1. **Node version**: run `node -v` to confirm engine compatibility.
2. **Ink and React versions**: run `npm ls ink react --depth=0` to determine if migration is needed.
3. **Module system**: confirm ESM (`"type": "module"`) vs CommonJS.
4. **TypeScript**: check for `tsconfig.json` and `@types/react` presence.
5. **Test setup**: verify `ink-testing-library` is installed and configured.
6. **Environment**: determine if the CLI runs in TTY (interactive) vs CI/piped (non-interactive).

## Start Here

1. Classify the request:
   - New project bootstrap.
   - Existing project migration.
   - Feature implementation.
   - Debugging or test failures.
2. Read [references/official-sources.md](references/official-sources.md) first for the verified version baseline.
3. Read only the reference file needed for the current subtask:
   - API surface: [references/api-v6.md](references/api-v6.md)
   - Bootstrapping or migration: [references/bootstrap-and-migration.md](references/bootstrap-and-migration.md)
   - Testing or rendering/debug behavior: [references/testing-and-debugging.md](references/testing-and-debugging.md)
   - Component ecosystem decisions: [references/component-ecosystem.md](references/component-ecosystem.md)
   - Legacy source reconciliation: [references/legacy-merge-map.md](references/legacy-merge-map.md)

## Workflow

### 1. Confirm Runtime and Dependency Baseline

Run version checks before writing or changing code:

```bash
node -v
npm ls ink react --depth=0
```

If `ink` is below `6.x` or `react` is below `19.x`, treat it as a migration task and use [references/bootstrap-and-migration.md](references/bootstrap-and-migration.md).

### 2. Choose Bootstrap Strategy

- Prefer direct modern setup or a template that already targets Ink v6 + React 19.
- If using `create-ink-app`, treat it as a shell scaffold and immediately upgrade dependencies because its shipped templates can lag behind latest Ink.
- Keep ESM (`"type": "module"`) and verify Node engine compatibility.

### 3. Implement UI with Ink Core + Stable Patterns

- Use core primitives first: `<Box>`, `<Text>`, `<Static>`, `<Spacer>`, `<Transform>`, `<Newline>`.
- For input-heavy flows, combine:
  - `useInput` for key events and navigation.
  - `usePaste` for full pasted payload handling.
  - `useFocus`/`useFocusManager` for keyboard-accessible focus models.
- For terminal-aware layout and cursor behavior, use:
  - `useBoxMetrics` for measured width/height/position.
  - `useWindowSize` for responsive layout.
  - `useCursor` for IME and cursor placement correctness.

### 4. Configure Render Behavior Deliberately

Use `render()` options according to environment:

- Interactive local app: keep `interactive: true` (default in TTY).
- CI or piped output: understand non-interactive behavior and final-frame-only semantics.
- Enable `kittyKeyboard` only when you need richer key semantics (`eventType`, extra modifiers).
- Use `concurrent: true` only when you rely on Suspense/transitions and are ready for changed render timing.

For static output generation (docs, file output, deterministic snapshots), use `renderToString()` instead of `render()`.

### 5. Test and Debug Before Claiming Done

- Use `ink-testing-library` for frame-level assertions and stdin simulation.
- Prefer focused behavior assertions:
  - navigation
  - submit/cancel
  - paste handling
  - resize/reflow behavior
- Add one CI-safe non-interactive test path for commands that may run in pipelines.
- Use [references/testing-and-debugging.md](references/testing-and-debugging.md) for checklists and failure triage.

## Examples

**Migrate from Ink v5 to v6:**
```bash
node -v
npm ls ink react --depth=0
# If ink < 6 or react < 19, read references/bootstrap-and-migration.md
# Upgrade dependencies, update imports, switch to new hooks where needed.
```

**Add paste handling and focus management:**
```tsx
import {useInput, usePaste, useFocusManager} from 'ink';

const App = () => {
  const {focusNext} = useFocusManager();
  usePaste((text) => {
    // handle pasted text
  });
  useInput((input, key) => {
    if (key.tab) focusNext();
  });
};
```

## Implementation Rules

- Keep user-facing text in `<Text>` nodes.
- Avoid mixing `console.*` with ad-hoc terminal writes unless behavior is intentional.
- Guard all terminal-specific behavior for non-interactive mode.
- For migration PRs, separate dependency upgrades from behavior changes when possible.
- Treat unverified "latest API" claims as stale until checked against [references/official-sources.md](references/official-sources.md).

## Output Expectations

When using this skill to deliver code or guidance, produce:

1. The detected version matrix (`node`, `ink`, `react`).
2. The chosen path (new build vs migration).
3. The specific APIs used (`useInput`, `usePaste`, `useBoxMetrics`, etc.).
4. The tests run and what behavior they validate.
5. Any remaining blockers (for example terminal capability limitations).

# Testing and Debugging

## Testing Stack

Use `ink-testing-library` as the primary test surface for Ink apps.
Target behavior, not implementation details.

## Core Testing Pattern

```tsx
import {render} from 'ink-testing-library';

test('renders and exits on q', () => {
  const {lastFrame, stdin, unmount} = render(<App />);

  expect(lastFrame()).toContain('Press q to quit');

  stdin.write('q');
  unmount();
});
```

## What to Assert

1. Initial frame content (`lastFrame()`).
2. State transitions after key input (`stdin.write(...)`).
3. Exit behavior (`waitUntilExit()` or explicit unmount).
4. Re-render correctness (`rerender(...)`) where props change.

## Suggested Test Matrix

- Navigation keys (up/down/left/right)
- Confirm/cancel keys (enter/escape)
- Paste flows (`usePaste` path)
- Focus movement (tab / shift+tab)
- Resize-driven layout logic (when using `useWindowSize`)
- Non-interactive output behavior (pipe/CI)

## Debug Workflow

### 1) Reproduce in Minimal Surface

- Keep only one component tree branch.
- Remove third-party UI wrappers temporarily.
- Verify issue with pure Ink primitives first.

### 2) Check Render Mode Assumptions

- Is this running in a TTY?
- Is `interactive` on/off intentionally?
- Is `kittyKeyboard` expected by your key handling code?

### 3) Check Stream Wiring

- Confirm `stdout`, `stdin`, `stderr` are not unexpectedly overridden.
- Verify any direct stream writes (`useStdout().write`, `useStderr().write`) are intentional.

### 4) Check Timing and Flush

- For timing-sensitive assertions, prefer waiting for render flush (`waitUntilRenderFlush`) before asserting final frame.
- Avoid brittle tests that depend on transient intermediate frames.

## Frequent Failure Patterns

1. Mixing `console.log` spam with Ink rendering and reading broken snapshots.
2. Assuming enhanced key metadata exists without `kittyKeyboard` support.
3. Testing only interactive mode and shipping broken non-interactive behavior.
4. Using stale scaffold dependencies where runtime and test behavior do not match v6 APIs.

## CI Guardrails

- Keep one smoke test per command in non-interactive mode.
- Keep one interaction test per critical flow in interactive mode.
- Fail fast on dependency drift (`npm ls ink react ink-testing-library --depth=0`).

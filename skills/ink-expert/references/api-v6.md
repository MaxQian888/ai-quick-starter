# Ink v6 API Snapshot

Use this file for day-to-day implementation guidance.
For strict source-of-truth checks, pair it with `official-sources.md`.

## Runtime Baseline

- Node: `>=20`
- React: `>=19.1.1`
- Ink package family currently tracked here: `6.8.0`

## Core Components

- `<Box>`: flex layout container
- `<Text>`: styled text node container
- `<Static>`: immutable historical output area
- `<Transform>`: output string transformation wrapper
- `<Spacer>`: flex spacer in row/column layouts
- `<Newline>`: explicit line breaks

## Hooks (Current Surface)

### Interaction and Focus

- `useInput(handler, options?)`
- `usePaste(handler, options?)`
- `useFocus(options?)`
- `useFocusManager()`

### Streams and Lifecycle

- `useApp()`
- `useStdin()`
- `useStdout()`
- `useStderr()`

### Accessibility and Layout Metrics

- `useIsScreenReaderEnabled()`
- `useBoxMetrics()`
- `useWindowSize()`
- `useCursor()`

## Render APIs

### `render(tree, options?)`

Use for interactive CLIs and live terminal apps.

Important options to reason about:

- `interactive`
- `kittyKeyboard`
- `concurrent`
- `stdout` / `stdin` / `stderr`
- `exitOnCtrlC`
- `patchConsole`
- `isScreenReaderEnabled`
- `maxFps`

### `renderToString(tree, options?)`

Use for deterministic or non-interactive output generation.
Prefer this in build scripts or snapshot-generation tasks.

## Instance Methods

Use the returned instance from `render()` for controlled runtime behavior:

- `rerender(nextTree)`
- `unmount()`
- `clear()`
- `waitUntilExit()`
- `waitUntilRenderFlush()`

## Input Details and Kitty Keyboard Protocol

When `kittyKeyboard` is enabled, `useInput` can expose richer key metadata.
Commonly used fields include:

- `key.option`
- `key.home`
- `key.end`
- `key.super`
- `key.hyper`
- `key.capsLock`
- `key.numLock`
- `key.scrollLock`
- `key.keycode`
- `key.eventType`

Keep fallback handling for terminals that do not support enhanced key reporting.

## Practical Patterns

1. Build navigation with `useInput` + `useFocusManager`.
2. Add explicit paste support with `usePaste` for multiline content.
3. Use `useWindowSize` to reflow columns/tables on resize.
4. Use `useBoxMetrics` only after mount when dimensions are stable.
5. Use `useCursor` when implementing custom text input UX.
6. Use `renderToString` for output that should not depend on TTY capabilities.

## Migration Notes from Older Ink Skills

Legacy skill snippets often miss these v6-era capabilities:

- `usePaste`
- `useBoxMetrics`
- `useWindowSize`
- `useCursor`
- `renderToString`
- `waitUntilRenderFlush`
- expanded key metadata under `kittyKeyboard`

When you see older guidance without these APIs, treat it as incomplete.

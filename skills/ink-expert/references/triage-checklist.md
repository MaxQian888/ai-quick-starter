# Triage Checklist

Use this checklist before proposing fixes.

## Step 1: Identify Baseline

- Node version:
- Ink version:
- React version:
- Is TTY interactive:
- Is `kittyKeyboard` enabled:

## Step 2: Classify Failure Type

- Layout (`Box` sizing, wrapping, clipping)
- Input (`useInput`, key mapping, paste)
- Focus (`useFocus`, `useFocusManager`)
- Stream/render (`stdout`/`stdin`, interactive mode)
- Test-only drift (`ink-testing-library`, snapshots)
- Dependency drift (old scaffold versions)

## Step 3: Minimal Reproduction

- Create smallest component tree that reproduces issue.
- Remove third-party components; re-add one by one.
- Verify behavior in both local terminal and CI-like non-interactive mode.

## Step 4: Fix Strategy

- Dependency mismatch: resolve versions first.
- Input mismatch: explicitly handle key/paste pathways.
- Layout mismatch: inspect `useWindowSize` and container widths.
- Rendering mismatch: choose `render` vs `renderToString` correctly.

## Step 5: Verify

- Rerun focused tests.
- Rerun end-to-end CLI command.
- Confirm output in interactive and non-interactive contexts.
- Document residual limitations (terminal capability or platform-specific behavior).

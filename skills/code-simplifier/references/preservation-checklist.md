# Preservation Checklist

Run this mental checklist before and after simplifying code.

## Public Contract

- Exports and import paths stay stable.
- Function signatures, prop names, and return shapes stay stable.
- Error types, messages, and fallback behavior stay stable unless the user asked for change.

## Runtime Behavior

- Side-effect order does not change.
- Async sequencing and awaited boundaries do not change accidentally.
- Conditional branches still cover the same cases.
- Validation and edge-case handling still run on the same inputs.

## State And UI

- React state ownership and effect timing stay stable.
- Rendered structure, accessibility labels, and user-visible copy stay stable unless intentionally changed.
- Derived values and memoized behavior keep the same inputs and outputs.

## Data Flow

- Input normalization still happens before use.
- Default values and null handling still match previous behavior.
- Logging, analytics, and callbacks still fire on the same paths.

## Verification

- Re-run the narrowest check that proves the simplified path still behaves correctly.
- Widen verification only after the local path is clean.
- If no automated check exists, report that gap explicitly.

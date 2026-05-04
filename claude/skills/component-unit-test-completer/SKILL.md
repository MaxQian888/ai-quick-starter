---
name: component-unit-test-completer
description: >
  Make sure to use this skill whenever the user wants to add missing component
  tests, complete unit test coverage, enforce one-to-one component/test mapping,
  or set up test coverage gates. Also trigger when they mention "write tests for
  my components," "increase test coverage," "missing component tests," "test
  coverage is too low," "add RTL tests," or "set up Vitest/Jest coverage."
  Covers synonyms like "unit test completion," "test gap analysis," "coverage
  enforcement," "component testing," "test scaffolding," and "UI test audit."
  Use it even when the user only says "I need tests" or "my components aren't
  tested" without specifying the framework.
---

# Component Unit Test Completer

Bring a frontend project to one canonical unit test per component, with behavior-driven assertions, enforced by a coverage gate. Work in the order: **map gaps → fill assertions → enforce gate**. Skipping the mapping step leads to coverage that looks fine in aggregate but hides untested components.

## Run scripts

The bundled scripts target Python 3.11+. Use `uv` if available; fall back to a system Python:

```bash
# Preferred:
uv run --python 3.11 scripts/component_test_map.py --root .

# Fallback when uv is not installed:
python3 scripts/component_test_map.py --root .
```

If both fail, install uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`) before continuing — the scripts have no third-party deps, so any Python ≥3.10 works.

## Step 1 — Detect the test ecosystem

Read `package.json` and the test config files to lock in the right vocabulary before generating anything. Capture:

- **Runner:** `vitest`, `jest`, or other — drives scaffold imports and the coverage command.
- **Library:** `@testing-library/react`, `vue/test-utils`, `enzyme` — drives assertion style.
- **Coverage config:** `vitest.config.*`, `jest.config.*`, `.nycrc`, or thresholds inside `package.json`. Note the existing reporter (`json-summary`, `lcov`) — `check_coverage_threshold.py` reads either.
- **Component conventions:** extensions in use (`.tsx`, `.jsx`, `.vue`, `.svelte`) and whether tests sit co-located, in `__tests__/`, or under a mirrored `tests/` tree.
- **CI gates:** any existing thresholds in `.github/workflows/` so the new gate is consistent with what CI already enforces.

If `coverage-summary.json` is not currently emitted, add `'json-summary'` to the reporter list — it's what produces per-file diagnostics in step 5.

## Step 2 — Discover mapping gaps

```bash
uv run --python 3.11 scripts/component_test_map.py --root .
```

Read the report and act on each bucket:

- `missing` — no test file matches the component. Either author the test or scaffold and immediately fill it (step 3).
- `duplicates` — multiple test files map to one component. Pick the canonical file, merge unique assertions into it, then delete the extras.
- `orphan_tests` — a test file matches no component by naming convention. Either rename it to match the component, move it into an integration/e2e folder excluded from this audit, or delete it if it's stale.

The script handles `Foo/index.tsx` patterns: a test named `Foo.test.tsx` (sibling or one level up) is accepted, not just `index.test.tsx`. It also excludes common non-source dirs (`node_modules`, `dist`, `coverage`, `e2e`, `cypress`, `playwright`, `__mocks__`, `storybook-static`).

## Step 3 — Scaffold only when it speeds you up

```bash
uv run --python 3.11 scripts/component_test_map.py --root . --scaffold-missing
```

Scaffolds use `it.todo(...)` so the runner reports them as pending — they will not silently pass and inflate coverage. The runner is auto-detected from `package.json` (`vitest` vs `jest`); override with `--framework jest`. **Never commit a scaffold with `it.todo` left in.** Replace each one with real assertions before opening a PR.

## Step 4 — Fill behavior assertions, one component at a time

Maintain one component → one canonical test file. For each component, cover at minimum:

- Happy-path render and the primary user interaction.
- Branch states the component can express: loading, empty, error, disabled, permission-gated, controlled-vs-uncontrolled.
- Callbacks and prop-driven side effects (assert what the parent observes, not internal state).
- Accessibility-critical behavior (role/name lookup, keyboard focus, `aria-*`) when the component participates in keyboard navigation or assistive tech.

Behavior > implementation: if you find yourself reading internal state, look for the user-visible signal instead. Reserve mocks for unstable boundaries (network, time, randomness, browser-only APIs); mocking too much hides the bug the test is supposed to catch.

Avoid snapshot-only suites unless the repo already depends on snapshots — they fail loudly on cosmetic changes and quietly on behavior changes.

## Step 5 — Run tests with coverage and enforce the gate

Use whatever the project already runs. Common forms:

```bash
npm test -- --coverage
pnpm test --coverage
vitest run --coverage
```

Then enforce the gate. `--per-file` surfaces the specific files dragging the metric down so you can target real fixes instead of guessing:

```bash
uv run --python 3.11 scripts/check_coverage_threshold.py --root . --threshold 80 --per-file
```

When the gate fails, prioritize **branch and function** coverage. Adding asserts that only re-execute already-covered lines wastes time; covering an untested `if/else` branch or an unreachable callback usually moves both metrics.

The 80% default is a starting point — match the project's existing standard if one is documented in `package.json` or the coverage config, and prefer raising the floor incrementally over backfilling everything at once.

## Mapping rules (reference)

- A component is a file with a configured component extension that is not a test (`.test.`, `.spec.`), story (`.stories.`, `.story.`), or declaration (`.d.`), and not under `__tests__/`.
- Accepted test locations:
  - Co-located: `<Component>.test.*` or `<Component>.spec.*`
  - Sibling test dir: `__tests__/<Component>.test.*` or `__tests__/<Component>.spec.*`
  - Mirrored root: `tests/<same-relative-path>/<Component>.test.*` or `.spec.*`
  - Index pattern: `Foo/index.tsx` accepts any of the above plus `Foo/Foo.test.tsx` and `Foo.test.tsx` one directory up.
- Exactly one canonical test file per component in the final state. Resolve duplicates by merging assertions, then deleting the redundant entry points.

## Guardrails

- Prefer the project's existing test stack. Do not introduce a new framework to satisfy this skill.
- Keep assertions behavior-oriented; snapshot suites and over-mocked tests both undermine the gate.
- Keep test names explicit (`renders error banner when fetch rejects`) so missing behavior is greppable in CI logs.
- Treat scaffold-with-`it.todo` as half-done work, not "covered."

## Examples

**Discover gaps only:**
```bash
uv run --python 3.11 scripts/component_test_map.py --root .
```

**Scaffold, run, enforce:**
```bash
uv run --python 3.11 scripts/component_test_map.py --root . --scaffold-missing
vitest run --coverage
uv run --python 3.11 scripts/check_coverage_threshold.py --root . --threshold 80 --per-file
```

**JSON output for CI consumption:**
```bash
uv run --python 3.11 scripts/component_test_map.py --root . --json-out .ci/test-map.json --strict-orphans
```

## References

- Execution checklist: `references/unit-test-completion-checklist.md`
- Linked skills (build, e2e, commit): `references/linked-skills.md`
- Mapping checker: `scripts/component_test_map.py`
- Coverage gate: `scripts/check_coverage_threshold.py`

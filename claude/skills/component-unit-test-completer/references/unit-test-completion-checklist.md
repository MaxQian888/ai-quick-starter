# Unit Test Completion Checklist

Use this checklist when closing a component unit test completion task.

## 1. Mapping completeness

- Run `uv run --python 3.11 scripts/component_test_map.py --root .` (or `python3 scripts/component_test_map.py --root .` if uv is unavailable).
- Confirm `missing: 0`.
- Confirm `duplicates: 0`.
- If `orphan_tests > 0`, decide for each whether it belongs in an excluded folder (integration/e2e/helper), should be renamed to match the component, or removed.

## 2. One component, one canonical test

- Keep exactly one canonical unit-test entry file per component.
- For `Foo/index.tsx`, prefer either `Foo/index.test.tsx` (mirrors the file) or `Foo/Foo.test.tsx` (mirrors the public name) — pick one and stay consistent within the repo.
- Merge assertions from duplicate files into the canonical file, then delete the extras.
- Match the repo's existing naming convention (`.test` vs `.spec`).

## 3. Assertion quality

- One happy-path render+interaction per component.
- Cover meaningful branches: loading, empty, error, disabled, permission, controlled vs uncontrolled.
- Assert user-visible behavior and callback effects, not internal state.
- Include accessibility checks (role/name/keyboard focus) when the component participates in keyboard nav or assistive tech.
- No `it.todo` placeholders left in committed code — they signal incomplete work, not coverage.

## 4. Coverage gate

- Ensure the project emits either `coverage/coverage-summary.json` (Vitest/Jest with `json-summary` reporter) or `coverage/lcov.info`.
- Run project tests with coverage enabled.
- Run `uv run --python 3.11 scripts/check_coverage_threshold.py --root . --threshold 80 --per-file`.
- When a metric fails, address branch/function gaps first — those move the needle more than line-only additions.

## 5. Final acceptance

- Mapping report passes.
- Coverage gate passes (or the failure is escalated with a concrete list of files to fix, from `--per-file`).
- New/updated tests are deterministic — no real network, time, or random sources unmocked.
- The added or modified test names read clearly enough that a CI log scan reveals what is missing.

# Tests

This directory contains test cases and validation scripts for the Ink CLI skill.

## Test Cases

1. **Version Detection** — Verify that Ink and React versions are correctly read from package.json.
2. **Component Rendering** — Validate that Box, Text, Static, and common patterns render expected frames.
3. **Input Handling** — Simulate keyboard input and assert navigation behavior.
4. **Migration Path** — Given an Ink v5 project, verify the v6 migration steps are accurate.

Use `ink-testing-library` for frame-level assertions in real Ink projects.

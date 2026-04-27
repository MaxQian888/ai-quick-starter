# Tests

This directory contains test cases for the writing-safe-shell-commands skill.

## Test Cases

1. **Risk classification** — Verify destructive requests are classified as high or blocked.
2. **Shell-specific traps** — Confirm path separators, quoting, and variable expansion are called out correctly.
3. **Staged commands** — Ensure high-risk work is split into Pre-check, Preview, Execute, and Verify stages.
4. **Cross-platform safety** — Validate PowerShell vs cmd vs bash decisions are appropriate.

Add tests here as the skill evolves.

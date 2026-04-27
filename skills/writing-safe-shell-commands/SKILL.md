---
name: writing-safe-shell-commands
description: |
  Use whenever you need to generate, review, or harden shell commands for PowerShell, cmd, or bash with safety and cross-platform guardrails. Make sure to use this skill whenever the user asks for a "command", "shell command", "bash one-liner", "PowerShell command", "terminal command", "script", or "how do I" for any filesystem, process, network, or system operation — even for seemingly simple commands like "delete files" or "find and replace". Also trigger when the user needs to run destructive operations, recursive commands, or environment mutations. If the user actually needs a reusable PowerShell script or module, use `powershell-writing-assistant` instead. Covers command generation, risk classification, staged execution, and cross-platform safety.
---

# Writing Safe Shell Commands

## Overview

Turn natural-language requests into shell-correct command sequences with explicit shell choice, risk staging, and verification.
Use this skill for command generation and hardening. If the user actually needs a reusable PowerShell script or module, use `powershell-writing-assistant` instead.

## Adaptive Detection

Before generating commands, detect the context:

1. **Target shell**: Determine if the user prefers PowerShell, cmd, bash, or zsh.
2. **Operating system**: Note Windows, macOS, Linux, or WSL constraints.
3. **Risk level**: Classify the request as read-only, state-changing, or destructive.
4. **Environment**: Check for elevated privileges, restricted shells, or container contexts.
5. **Existing tools**: Note if the user has `ripgrep`, `fd`, `fzf`, or other modern CLI tools installed.

Use these signals to choose safe syntax and appropriate guardrails.

## Workflow

1. Identify the target shell. Preserve the user's requested shell unless it would make the command less safe or less clear. Load `references/shell-selection.md` when shell choice or syntax is uncertain.
2. Classify the request as `low`, `medium`, `high`, or `blocked`. Load `references/risk-triage.md` before giving any destructive or state-changing command.
3. Build the answer in this order:
   1. `Shell`
   2. `Risk`
   3. `Pre-check`
   4. `Preview`
   5. `Execute`
   6. `Verify`
   7. `Notes`
4. Use `references/safe-command-patterns.md` to split risky work into reviewable command stages.
5. Use `references/dangerous-command-catalog.md` whenever a request involves recursive deletion, force overwrite, process termination, environment mutation, or other broad side effects.
6. Run `references/review-checklist.md` before returning the final command sequence.

## Output Rules

- For `low` risk, direct commands are acceptable, but still choose the shell explicitly and quote paths correctly.
- For `medium` risk, require at least `Pre-check`, `Execute`, and `Verify`.
- For `high` risk, require `Pre-check`, `Preview`, `Execute`, and `Verify`. Do not lead with the destructive command.
- For `blocked`, do not provide an execution command. Explain why the target is unsafe or underspecified and provide only boundary-discovery or read-only inspection commands.
- Call out shell-specific traps when they matter: path separators, variable expansion, wildcard expansion, quoting, encoding, and privilege boundaries.

## Examples

### Example 1: Low-risk file listing

```bash
Shell: bash
Risk: low
Pre-check: ls -la /path/to/dir
Execute: find /path/to/dir -name "*.log" -type f
Verify: echo "Found $(find /path/to/dir -name '*.log' -type f | wc -l) log files"
```

### Example 2: High-risk recursive deletion

```bash
Shell: bash
Risk: high
Pre-check: find . -type d -name "node_modules" | head -5
Preview: find . -type d -name "node_modules" | wc -l
Execute: find . -type d -name "node_modules" -prune -exec rm -rf {} +
Verify: find . -type d -name "node_modules" | wc -l  # should be 0
Notes: Run from the project root. This is destructive and irreversible.
```

## Reference Files

- `references/risk-triage.md`: Load for low / medium / high / blocked classification and minimum response shape.
- `references/shell-selection.md`: Load for PowerShell vs `cmd` vs `bash` decisions and syntax pitfalls.
- `references/safe-command-patterns.md`: Load for staged command templates such as list-first, preview-then-act, and verify-after.
- `references/dangerous-command-catalog.md`: Load when the request touches destructive, recursive, or high-blast-radius command families.
- `references/review-checklist.md`: Load as the final self-audit before returning the command sequence.

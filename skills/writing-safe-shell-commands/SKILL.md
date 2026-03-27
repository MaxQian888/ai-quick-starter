---
name: writing-safe-shell-commands
description: Generate, review, and harden shell commands for PowerShell, cmd, and bash. Use when Codex needs to turn natural-language tasks into executable commands, especially when commands may fail because of quoting, paths, globbing, shell differences, or when operations are destructive, high-impact, or need preview and confirmation steps before execution.
---

# Writing Safe Shell Commands

## Overview

Turn natural-language requests into shell-correct command sequences with explicit shell choice, risk staging, and verification.
Use this skill for command generation and hardening. If the user actually needs a reusable PowerShell script or module, use `powershell-writing-assistant` instead.

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

## Reference Files

- `references/risk-triage.md`: Load for low / medium / high / blocked classification and minimum response shape.
- `references/shell-selection.md`: Load for PowerShell vs `cmd` vs `bash` decisions and syntax pitfalls.
- `references/safe-command-patterns.md`: Load for staged command templates such as list-first, preview-then-act, and verify-after.
- `references/dangerous-command-catalog.md`: Load when the request touches destructive, recursive, or high-blast-radius command families.
- `references/review-checklist.md`: Load as the final self-audit before returning the command sequence.

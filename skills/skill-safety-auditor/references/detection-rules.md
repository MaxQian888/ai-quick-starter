# Detection Rules

## Risk Categories

- `hardcoded-secret`: real-looking keys, tokens, passwords, or credential literals embedded in skill files.
- `dangerous-command`: destructive shell commands, shell-eval patterns, or irreversible git/file operations.
- `outside-workspace-write`: instructions to write to absolute paths outside the current workspace.
- `unguarded-network-or-production-action`: production or network-facing commands without dry-run or confirmation guardrails.
- `trigger-too-broad`: descriptions that can activate for almost any coding task.
- `missing-runtime-verification`: script-backed skills without supported tests or an explicit runtime verification contract.

## Secret Heuristics

- Flag env-var assignments or inline literals that look reusable.
- Ignore obvious placeholders such as `<YOUR_API_KEY>`, `changeme`, or `example`.
- Prefer redacted evidence in reports instead of echoing the full value.

## Dangerous Command Heuristics

- Flag direct destructive patterns such as `rm -rf /`, `Remove-Item -Recurse -Force`, `git reset --hard`, `git checkout --`, `curl | sh`, and shell-eval helpers.
- Treat these as blocked until they are replaced with preview-first guarded workflows.

## Outside-Workspace Write Heuristics

- Flag absolute write destinations outside the workspace root.
- Prefer repository-relative destinations or explicit human-confirmed external paths.

## Trigger Heuristics

- Flag descriptions containing broad phrases such as `any code`, `any repository`, `any task`, `anything`, or `general purpose`.
- Prefer triggers that mention one concrete task shape, artifact type, or risk context.

## Verification Heuristics

- Treat a skill as script-backed when `scripts/` contains executable files.
- Accept `tests/test_*.py`, `tests/*.test.mjs`, `tests/test_*.mjs`, `tests/*.Tests.ps1`, or `tests/runtime-verification.json` as supported verification surfaces.
- If none exist, report the gap instead of assuming the scripts are safe.

# Remediation Guidelines

## Narrow Trigger Descriptions

- Replace broad phrases with one concrete task shape.
- Mention the artifact being inspected, not generic coding work.
- Keep the description focused on when to use the skill, not how it works.

## Replace Dangerous Commands

- Prefer preview, path validation, confirmation, then execution.
- Replace direct destructive examples with guarded command sequences.
- Avoid shell-eval forms such as `curl | sh`, `Invoke-Expression`, or hidden irreversible git resets.

## Remove Or Mask Secrets

- Replace real values with obvious placeholders.
- Keep instructions environment-variable based.
- Never preserve a real-looking secret as an example value.

## Constrain Writes

- Prefer relative paths inside the current repository.
- If an external destination is required, make it explicit that a human must confirm the path first.
- Do not silently promote global paths such as `~/.ssh`, `~/.codex`, or system directories as defaults.

## Add Verification Surfaces

- Add `tests/` for script-backed helpers whenever possible.
- If the runtime contract is unusual, provide `tests/runtime-verification.json`.
- Treat missing verification as a trust gap, not as optional polish.

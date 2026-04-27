# CLI Adapters

Use this file after the loop pattern is chosen and the user names the target runner.

Validated on 2026-03-29 against local `claude --help`, local `codex --help`, local `codex exec --help`, local `codex exec resume --help`, and the official OpenCode CLI docs at `https://opencode.ai/docs/cli/`.

## Shared Mapping

| Need | Claude Code | Codex CLI | OpenCode |
| --- | --- | --- | --- |
| Interactive session | `claude` | `codex` | `opencode` |
| One-shot non-interactive run | `claude -p "..."` | `codex exec "..."` | `opencode run ...` |
| Continue last session | `claude -c` or `claude -c -p "..."` | `codex exec resume --last "..."` | `opencode run --continue ...` |
| Resume named session | `claude -r <id>` | `codex exec resume <session-id> "..."` | `opencode run --session <id> ...` |
| Fork while resuming | `claude --fork-session ...` | use a fresh run or separate fork workflow | `opencode run --fork --continue ...` or `--fork --session <id>` |
| Structured event output | `claude -p --output-format json` | `codex exec --json` | `opencode run --format json` |

## Claude Code

Use when the environment and skill stack are already Claude-oriented.

Important flags:
- `-p` for non-interactive execution.
- `-c` to continue the most recent conversation in the current directory.
- `-r` to resume a specific session.
- `--allowedTools` or `--tools` when the loop needs a restricted tool surface.
- `--permission-mode` when the operator needs a specific permission profile.

Good fit:
- existing `.claude` command or skill ecosystems,
- interactive work that may later be promoted into loopable `-p` passes,
- resume-heavy workflows.

## Codex CLI

Use when the operator wants explicit sandbox and approval controls.

Important flags:
- `exec` for non-interactive runs.
- `exec resume --last` to continue the latest recorded session.
- `--full-auto` for low-friction sandboxed execution.
- `--sandbox read-only|workspace-write|danger-full-access` for command execution policy.
- `--ask-for-approval ...` when the approval threshold matters.
- `--skip-git-repo-check` when the working directory is not a Git repository root.
- `--json` for machine-readable event output.

Good fit:
- repo repair or automation that benefits from explicit sandboxing,
- runs outside a Git root where you still want controlled execution,
- workflows that need structured event capture.

## OpenCode

Use when the operator wants a lightweight non-interactive runner, reusable local server attachment, or compatibility with existing `.claude` skills.

Important flags from the official docs:
- `run` for non-interactive execution.
- `--continue` or `--session <id>` to continue prior work.
- `--fork` to continue while branching the session state.
- `--format json` for raw event output.
- `--attach http://host:port` to reuse a running `opencode serve` instance.
- `serve` when repeated runs should avoid backend cold starts.

OpenCode-specific note:
- By default it can read `.claude` prompts and skills unless the operator disables that behavior with `OPENCODE_DISABLE_CLAUDE_CODE*` environment variables. Use that compatibility deliberately.

Good fit:
- scriptable local loops that benefit from a warm reusable backend,
- environments already mixing Claude-style prompts with another runner,
- cases where session reuse matters but Codex-specific sandbox flags are not required.

## Adapter Rules

- Preserve the loop contract across CLIs: same task, same notes file, same verification gate.
- Re-check permission and sandbox assumptions every time the CLI changes.
- Prefer local `--help` output over memory when the runner is installed.
- If one CLI lacks a safety control available in another, say so instead of pretending the flags are equivalent.

# Codex Subagents Notes

Use this file when you need Codex-specific context instead of generic "multi-agent" advice.

## Config Layout

- Shared runtime controls such as `multi_agent`, `max_depth`, and `max_threads` live in the main Codex config.
- Per-agent configuration belongs in separate files under `~/.codex/agents/<name>.toml`.
- Treat generated `.toml` files as drafts until a human reviews them and copies them into place or explicitly uses install mode.
- For managed installs, write a manifest under `~/.codex/agents/.agents-team-builder/manifests/` and keep backups under the same tool-owned directory.

## Built-In Roles

Codex has three built-in role names worth planning around first:

- `default`: fallback synthesis and helper work
- `worker`: execution-focused implementation
- `explorer`: read-heavy exploration

Generate custom roles only when the task shape justifies them.

## Planning Caveats

- A role plan is not the same thing as actual runtime selection. Codex may still choose a different agent unless the operator invokes a specific role.
- More agents are not automatically better. Over-parallelization can slow the work down if the merge point is vague.
- The first-pass team plan should optimize for clear ownership, not for maximizing thread count.
- Uninstall should only touch files listed in a manifest created by this tool. If there is no manifest, the tool should refuse to guess.

## Official Sources To Refresh Against

- `https://developers.openai.com/codex/concepts/subagents`
- `https://developers.openai.com/codex/subagents`

If runtime behavior matters, refresh these docs before hardcoding new assumptions into the skill.

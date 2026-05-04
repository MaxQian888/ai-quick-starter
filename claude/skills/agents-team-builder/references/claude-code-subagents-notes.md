# Claude Code Subagent and Agent Team Notes

Read this file when the request targets Claude Code (`--target claude-code` or `--target both`) and generic "multi-agent" advice would lose details that the Claude Code platform actually cares about.

## Subagent File Format

Claude Code subagents are Markdown files with YAML frontmatter:

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices. Use proactively after writing or modifying code.
tools: Read, Glob, Grep, Bash
model: sonnet
color: purple
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

The frontmatter defines metadata; the body is the **system prompt** the subagent runs with. Subagents only receive this system prompt plus minimal environment context — not Claude Code's default system prompt.

## Required and Common Frontmatter Fields

- `name` (required): lowercase letters and hyphens only.
- `description` (required): when Claude should delegate to this subagent. Add "use proactively" phrases when you want eager delegation.
- `tools` (optional, allowlist): comma-separated tool names (`Read, Grep, Glob, WebFetch`). Inherits everything if omitted.
- `disallowedTools` (optional, denylist): tools to remove from the inherited or specified list.
- `model` (optional): `sonnet`, `opus`, `haiku`, a full model ID (`claude-opus-4-7`), or `inherit`. Defaults to `inherit`.
- `color` (optional): `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, or `cyan`. Used in the task list and transcript UI.

Less common but supported: `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `initialPrompt`. The skill leaves these alone by default; reach for them when the brief calls out a specific need (e.g. `permissionMode: plan` for a research-only role).

## Subagent Scope and Priority

When the same `name` appears in multiple locations, the higher-priority scope wins:

| Location | Scope | Priority |
| :--- | :--- | :--- |
| Managed settings (`.claude/agents/` inside managed settings dir) | Org-wide | 1 (highest) |
| `--agents` CLI JSON flag | Current session | 2 |
| `.claude/agents/` | Current project | 3 |
| `~/.claude/agents/` | All your projects | 4 |
| Plugin `agents/` directory | Where plugin is enabled | 5 (lowest) |

Project subagents (`.claude/agents/`) live next to the codebase and can be checked into version control. User subagents (`~/.claude/agents/`) follow the operator across projects. Use the project scope by default for team plans; user scope is right when the role is personal-productivity (e.g. a private code-reviewer).

## Agent Teams (Experimental)

Agent teams coordinate **multiple Claude Code sessions**. They differ from subagents:

- A subagent runs inside a single session and reports results back to the main agent.
- A teammate is its own Claude Code session that talks directly to other teammates and shares a task list.

Agent teams require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` and Claude Code v2.1.32 or later.

### Team Config Is Runtime State

`~/.claude/teams/<team-name>/config.json` is generated automatically when the lead spawns the team. It holds session IDs, tmux pane IDs, and other runtime data, and Claude Code overwrites it on the next state update. **Do not pre-author or hand-edit this file.** The skill therefore emits a paste-in **team brief** (Markdown) instead, which the user gives to a Claude Code lead.

There is no project-level equivalent of the team config — a `.claude/teams/teams.json` file inside the project is treated as an ordinary file, not configuration.

### Reusing Subagent Definitions As Teammates

When the lead spawns a teammate, it can reference a subagent type from any scope. The teammate honors that subagent's `tools` allowlist and `model`, and the subagent body is appended to the teammate's system prompt as additional instructions. The skill exploits this by generating subagent `.md` files and a brief that says "Spawn a teammate using the `<name>` subagent type".

Caveat: `skills` and `mcpServers` from the subagent definition are **not** applied when running as a teammate — those load from the operator's project and user settings as in any normal session. Plan accordingly when a role needs domain-specific skills.

### Display Modes

- `in-process` (default in plain terminals): all teammates share the lead's terminal. Use Shift+Down to cycle.
- `tmux`/split panes: requires tmux on Linux/macOS, or iTerm2 + the `it2` CLI. Not supported in VS Code's integrated terminal, Windows Terminal, or Ghostty.

The skill's brief stays display-mode-agnostic; the operator can override per-session with `claude --teammate-mode in-process`.

## Tool Selection Heuristics

Map the team plan's `sandbox_mode` to a Claude Code `tools` allowlist:

- `read-only` → `Read, Grep, Glob, WebFetch, WebSearch`. Good fit for explorer / reviewer / verifier roles.
- `workspace-write` → `Read, Edit, Write, Bash, Grep, Glob, WebFetch`. Reasonable default for implementer/worker/planner roles. Switch to `disallowedTools: Write, Edit` if the role should keep MCP access but still be read-only.

Tighten further with hooks (`PreToolUse` matchers) when a role needs conditional rules — for example, allowing Bash only for read-only SQL.

## Model Selection Heuristics

- `explorer` → `haiku` (fast, low-latency, cheap for read-heavy passes).
- `default`, `worker`, `implementer`, `planner`, `archiver`, `reviewer` → `sonnet` (balanced).
- Final-quality reviewers or critical synthesis → `opus` when latency and cost are acceptable.

The `--model` per-invocation override and `CLAUDE_CODE_SUBAGENT_MODEL` env var both win over the frontmatter, so don't assume the frontmatter alone determines runtime model.

## Planning Caveats

- A subagent definition isn't an automatic delegation guarantee. Claude decides based on description + context. Sharper descriptions ("use proactively for …") delegate more reliably.
- Subagents cannot spawn other subagents; nested workflows belong in skills or chained subagent calls from the main session.
- Token cost scales with team size. Start with 3–5 teammates and 5–6 tasks per teammate; raise only when the work is genuinely independent.
- Two teammates editing the same file leads to overwrites. Keep ownership boundaries explicit in the spawn brief.
- The lead is fixed for the team's lifetime — choose the right session as lead before spawning.

## Official Sources To Refresh Against

- `https://code.claude.com/docs/en/sub-agents`
- `https://code.claude.com/docs/en/agent-teams`
- `https://code.claude.com/docs/en/settings`

If runtime behavior matters, refresh these docs before hardcoding new assumptions into the skill — the agent-teams feature is explicitly experimental and changes shape between Claude Code releases.

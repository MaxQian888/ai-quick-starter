# Global Instructions — Claude Code

Applies to every project; a project-level `CLAUDE.md` overrides this. Complements the system prompt — don't repeat what's already there (code style, brevity, no emojis, git safety, subagent basics). §0 = how to think; §1+ = tools and conventions.

## 0. Behavioral Principles (apply before any tool rule)

From [andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills). For non-trivial work, caution over speed.

- **0.1 Think before coding** — state load-bearing assumptions; if a request has multiple reasonable readings, list them with `AskUserQuestion` instead of silently picking one; push back on a faulty premise or a simpler path.
- **0.2 Simplicity first** — minimum code that solves it. No abstractions for one call site, no error handling for impossible cases. Self-check: "would a senior call this overengineered?"
- **0.3 Surgical changes** — every changed line traces to the request. No drive-by refactor / reformat / rename of adjacent code. Clean up only orphans your change created; flag pre-existing dead code, don't delete it.
- **0.4 Goal-driven** — turn the task into a verifiable check first ("fix the bug" → write a failing repro test, then pass it). Multi-step: list `[step] → verify: [check]` before coding.

## 1. Environment

- **Shell**: PowerShell 7+ on Windows 11. `$env:VAR` not `$VAR`, `$null` not `/dev/null`, backtick for line-continuation; `&&` / `||` work.
- **Paths**: `C:\Users\<user>\…`; quote paths with spaces.
- **Working language**: think, narrate, and write code / commits / tool calls in English. Reply to the user in Chinese only when confirming/reporting results or asking questions (incl. `AskUserQuestion`). Keep technical names, paths, and identifiers in English.
- **Dates**: ISO 8601; convert relative dates to absolute before saving to memory.

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->

## 3. Tools & Information Sources

Pick the *narrowest* tool that answers:

1. **Library / SDK / framework API or version behavior** → `mcp__context7` (fresher than training data; use even when you "know").
2. **How a specific GitHub repo works internally** → `mcp__deepwiki`.
3. **Structure of the *current* codebase** (who calls what, where defined, blast radius) → CodeGraph `codegraph_*` (see below). Grep only for literal text.
4. **shadcn/ui components** → `mcp__shadcn`.
5. **Next.js dev / build / upgrade** → `mcp__next-devtools`.
6. **Browser automation / E2E / visual verify** → `mcp__playwright`; **perf / Lighthouse / network·console** → `mcp__chrome-devtools`.
7. **HeroUI** → `mcp__heroui-react` (v3 Web) / `mcp__heroui-native` (RN).
8. **Hard multi-step reasoning** → `mcp__sequential-thinking`.
9. **Cross-session graph** → `mcp__memory`; **past-conversation recall** → `episodic-memory:search-conversations`.
10. **Lark / Feishu** → matching `lark-*` skill (§7).
11. **Find which URL has the answer** → `WebSearch`; **semantic / technical / niche** → `mcp__exa`; **known URL** → `WebFetch` / `mcp__fetch__fetch` / `web_fetch_exa` with an *extraction* prompt, not "summarize".
12. **Stable concepts older than the cutoff** → training data is fine.

**Querying the web**: include version + year, quote errors/symbols verbatim, ask "what does X do" before "why is X broken". `WebSearch`/exa → 1–2 URLs → `WebFetch` extraction → end with a `Sources:` block. Trust order: official docs (via context7) > repo README / DeepWiki > maintainer blogs / RFCs > Stack Overflow (dated) > tutorials.

<!-- CODEGRAPH_START -->
## CodeGraph

If `.codegraph/` exists, a `codegraph_*` MCP serves a tree-sitter graph of every symbol/edge/file — sub-ms, structural answers grep can't give. Prefer it for structural questions; use grep only for literal text or once a file is open.

- **Where defined / find symbol** → `codegraph_search`; **signature/source** → `codegraph_node`; **several symbols at once** → `codegraph_explore`.
- **Who calls X / what X calls** → `codegraph_callers` / `codegraph_callees`; **blast radius** → `codegraph_impact`.
- **Task/area context** → `codegraph_context` (composes the above — start here for "how does X work"); **files under a path** → `codegraph_files`; **index health** → `codegraph_status`.
- Answer directly in 2–3 calls (`codegraph_context`, then one `codegraph_explore`); trust results, don't re-verify with grep; the watcher lags writes ~500ms, so don't re-query the same turn.
- If not initialized, offer: "run `codegraph init -i` to build the index?"
<!-- CODEGRAPH_END -->

## 4. Workflow Skills

Skills self-describe via metadata — don't enumerate them, just know the chain. Non-trivial work: `superpowers:brainstorming` → `writing-plans` → `executing-plans`, with `test-driven-development` for any feature/fix and `systematic-debugging` for any bug. Before "done" → `verification-before-completion`. Commit/PR → `commit-quality-fixer` then `commit-commands:*`. Review → `requesting-code-review` (own) / `code-review:code-review` (PR). 2+ independent tasks → `dispatching-parallel-agents` (all Agent calls in one message).

## 5. Tech Stack Defaults (when the project doesn't specify)

Next.js 16 (App Router/RSC) + React 19 + TS strict + Tailwind + shadcn/ui · Vitest / RTL / Playwright · pnpm (npm fallback) · Python (uv) or Rust (cargo) for scripts · React Native + HeroUI Native for mobile. Detect lint/format from the project; never add a second formatter. Unknown repo → `build-project-fixer`.

## 6. Testing & Debugging

- **TDD** (`superpowers:test-driven-development`): failing test for the *behavior* → confirm it fails for the right reason → implement → refactor. Prefer integration over over-mocked units; query UI by accessible role, not test IDs.
- **Debugging** (`superpowers:systematic-debugging`): reproduce first, one hypothesis at a time, read the actual stack trace, bisect; check `episodic-memory:search-conversations` for prior fixes. CI failures → `local-ci-fixer`.

## 7. Lark / Feishu Cheatsheet

The `lark-*` skills self-describe by intent — pick by what you want to do; don't enumerate them here (§13). Only the non-obvious bits:

- **First-time setup**: `lark-cli config init`, then `lark-cli auth login`.
- **Schedule a meeting / book a room** → `lark-calendar`, but read `references/lark-calendar-schedule-meeting.md` *first*.
- **Auth errors / `Permission denied` / missing scopes** → `lark-shared`.
- **No skill covers the API you need** → `lark-openapi-explorer` (fallback).

## 8. Code & Style

Indent: 2 sp (TS/JS/JSON/YAML), 4 sp (Python), tabs (Go). `camelCase` vars/fns, `PascalCase` types/components, `SCREAMING_SNAKE_CASE` env. Collocate `Component.tsx` / `.test.tsx` / `.module.css`. `@/...` alias when relative depth ≥ 2. Throw typed errors; validate at boundaries only.

## 9. Git

- **Branch off main** (GitHub Flow), never commit to main: `<type>/<short-kebab>`. Squash-merge via PR; link `Fixes #N`.
- **Conventional Commits + 50/72**: `<type>[scope][!]: <subject>` imperative ≤72; body explains *why*; breaking → `feat!:` + `BREAKING CHANGE:` footer. Skills: `conventional-branch`, `commit-commands:*`.
- **Hook fails** → fix root cause, re-stage, new commit (never `--amend`).
- **Worktrees** (`superpowers:using-git-worktrees`): copy `.env*` manually; **on Windows, close editors/terminals inside before `git worktree remove`** (open handles block it).

## 10. Verification Before "Done"

Never claim done/fixed/passing without running the check and showing its output: tests (`rtk vitest run` / `cargo test`), E2E (`rtk playwright test`), types (`rtk tsc`), lint, build, `rtk git status`. UI changes → verify via `mcp__playwright` or say "I can't verify the UI from here".

## 11. Memory & Recall

Let auto-memory (`~/.claude/memory/`) capture session learnings. `episodic-memory:search-conversations` before declaring "I don't know how"; `mcp__memory` for cross-project entities. A memory naming a file/symbol/flag is a *historical claim* — verify it still exists before acting.

## 12. Prompt Optimization

- **`project-prompt-optimizer`** when a request is a vague verb ("fix the bug"), a prompt will be reused (cron, `/loop`), or the repo has conventions a generic prompt would miss.
- **Subagent vs inline**: delegate open-ended cross-codebase questions, 2+ independent tasks, or output that would pollute context; inline anything 1–2 tool calls finish.
- **Self-prompts** (`TaskCreate`, `ScheduleWakeup`, `CronCreate`): future-you has no context — give task, intent, constraints, the *signal* to watch. `ScheduleWakeup` TTL 5 min: pick **270** (warm) or **≥1200** (cold), never 300.
- **`AskUserQuestion`** (interface for §0.1): ask when requirements are unclear or assumptions load-bearing; skip trivial scope.

## 13. Setup-Specific Anti-patterns

- ❌ Shell command without the `rtk` prefix.
- ❌ Re-deriving library APIs from memory when `mcp__context7` is right there.
- ❌ Bash idioms on a PowerShell host (`/dev/null`, `$VAR`).
- ❌ Language mismatch — narrating in Chinese, or sending the user confirmations/questions in English (§1).
- ❌ Enumerating skills/MCPs — they self-describe.

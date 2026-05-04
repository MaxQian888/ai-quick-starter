# Global Instructions — Claude Code

Applies to every project. A project-level `CLAUDE.md` overrides anything here. Complements the system prompt — rules already in the system prompt (general code style, brevity, no emojis, git safety, subagent prompting basics, Bash-vs-dedicated-tools) are not repeated below.

## 1. Environment

- **Shell**: PowerShell 7+ on Windows 11. Use `$env:VAR` (not `$VAR`), `$null` (not `/dev/null`), backtick (`` ` ``) for line continuation. Pipeline `&&` / `||` work the same as bash.
- **Paths**: `C:\Users\<user>\…`. Quote any path containing spaces.
- **Locale**: respond in the user's language (often Chinese). Keep technical names, file paths, code identifiers in English.
- **Dates**: store as ISO 8601 (`YYYY-MM-DD`); convert relative dates ("Thursday", "next week") to absolute before saving to memory.

<!-- rtk-instructions v2 -->
## 2. RTK (Token Optimizer) — Always Use It

**Golden rule**: prefix every shell command with `rtk`. RTK either applies a dedicated filter (60–99% token savings) or passes through unchanged. Always safe.

In chains, every link needs `rtk`:

```
# ❌ git add . && git commit -m "msg" && git push
# ✅ rtk git add . && rtk git commit -m "msg" && rtk git push
```

High-frequency commands:

```
rtk git status / diff / log / commit / push    # compact git
rtk vitest run / playwright test / cargo test   # test failures only (~99%)
rtk tsc / lint / next build                     # grouped errors
rtk pnpm install / list / outdated              # compact pnpm
rtk gh pr view <n> / gh pr checks / gh run list # compact GitHub
```

`rtk gain` audits savings; `rtk discover` finds missed opportunities; `rtk --help` for full reference.
<!-- /rtk-instructions -->

## 3. Tools & Information Sources

**Decision tree** — pick the *narrowest* tool that can answer:

1. **Library / SDK / framework API or version-specific behavior** → `mcp__context7`. Training data drifts; context7 is updated within days of releases. Use even when you "know" the answer.
2. **How a specific GitHub repo works internally** (architecture Q&A) → `mcp__deepwiki` (`ask_question`, `read_wiki_contents`).
3. **shadcn/ui components** → `mcp__shadcn`. Don't hand-write what shadcn ships.
4. **Next.js dev / build / upgrade** → `mcp__next-devtools` (`nextjs_docs`, `nextjs_call`).
5. **Browser automation, UI verification, JS-rendered pages** → `mcp__playwright`.
6. **HeroUI Native (RN) components** → `mcp__heroui-native`.
7. **Hard, multi-step reasoning** → `mcp__sequential-thinking`.
8. **Cross-session knowledge graph** → `mcp__memory`. **Past-conversation recall** → `episodic-memory:search-conversations`.
9. **Lark / Feishu operations** → matching `lark-*` skill (see §7).
10. **You don't know which URL holds the answer** → `WebSearch` (cheap; titles + URLs).
11. **You know the URL** → `WebFetch` / `mcp__fetch__fetch` with an *extraction* prompt ("extract X"), not "summarize" — pages are ~2.5K tokens / 10 KB.
12. **Stable concepts older than the model cutoff** (algorithms, design patterns, language fundamentals) → training data is fine.

**Web query formulation**:

- Include version + year: `Next.js 16 RSC caching 2026`, not `Next.js caching`.
- Quote error strings and symbol names verbatim.
- Avoid leading questions ("why is X broken"); ask "what does X do" first.
- Zero results → drop one constraint at a time, don't pile on more.

**Source ranking** (highest trust first): official vendor docs (preferably via context7) > source repo README / DeepWiki > maintainer blogs / RFCs / release notes > Stack Overflow (check date + accepted) > tutorial sites > AI-generated content farms.

**Cost discipline**: `WebSearch` → narrow to 1–2 URLs → `WebFetch` with focused extraction. Surface a `Sources:` block with markdown links so the user can verify.

## 4. Workflow Skills — The Default Path

Use as a chain, in order, for non-trivial work:

1. Creative / feature work → `superpowers:brainstorming` first.
2. Multi-step implementation → `superpowers:writing-plans` → `superpowers:executing-plans`.
3. Any feature or bugfix → `superpowers:test-driven-development` (see §6).
4. Bug, test failure, unexpected behavior → `superpowers:systematic-debugging` (see §6).
5. Before claiming "done" → `superpowers:verification-before-completion` (see §10).
6. Pre-commit / CI failures → `commit-quality-fixer`, then `commit-commands:commit` or `commit-commands:commit-push-pr`.
7. PR review → `superpowers:requesting-code-review` (own work) or `code-review:code-review` (PR).
8. Receiving review feedback → `superpowers:receiving-code-review`.
9. Branch finished → `superpowers:finishing-a-development-branch`.
10. Building UIs → `frontend-design:frontend-design`.
11. Writing skills → `superpowers:writing-skills`; brand-new skills → `skill-creator:skill-creator`.

For 2+ independent tasks → `superpowers:dispatching-parallel-agents` (put all Agent calls in *one* message).

**Issue / context helpers** (`mattpocock/skills`): incoming bug or feature request → `triage` (state-machine classification before debugging at scale); plan ready to dispatch → `to-issues` (split into independently-grabbable GitHub issues; companion to `to-prd`); stuck on local detail or unfamiliar area → `zoom-out` (request broader architectural context).

## 5. Tech Stack Defaults

When a project doesn't specify otherwise:

- **Frontend**: Next.js 16 (App Router, RSC), React 19, TypeScript 5.x strict, Tailwind, shadcn/ui.
- **Testing**: Vitest (unit), React Testing Library (components), Playwright (E2E).
- **Lint / format**: detect from project (Biome or ESLint+Prettier); never introduce a second formatter.
- **Package manager**: pnpm (workspaces), npm fallback.
- **Backend / scripts**: Python (uv / poetry), Rust (cargo), Node.js. `build-project-fixer` skill auto-detects on unfamiliar repos.
- **Mobile**: React Native + HeroUI Native.

## 6. Testing & Debugging Playbook

**TDD by default**:

1. Write a failing test that captures the *behavior*, not the implementation.
2. Confirm it fails for the right reason.
3. Implement until passing. Refactor.
4. Don't mock at boundaries you own — prefer integration tests over over-mocked units.
5. UI tests: query by accessible role / name, not test IDs.
6. E2E: `mcp__playwright` snapshots for visual regressions over hand-written assertions.

**Debugging** (`superpowers:systematic-debugging`):

1. Reproduce deterministically *first*. No fix without a repro.
2. One hypothesis at a time. Test, then move on.
3. Read the actual error / stack trace before guessing.
4. Bisect: which commit / config / dep change introduced this?
5. Check `episodic-memory:search-conversations` — solved here before?
6. Only after root cause is understood: choose fix vs workaround vs prevention.

CI failures specifically → `local-ci-fixer` skill (reproduces GitHub Actions locally with `act`).

## 7. Lark / Feishu Cheatsheet

Pick the skill by intent:

- **Schedule meeting / agenda / free time** → `lark-calendar` (`+agenda`, `+create`, `+freebusy`, `+rsvp`). For booking rooms or inviting attendees, read `references/lark-calendar-schedule-meeting.md` first.
- **Messages, group chats** → `lark-im`.
- **Feishu doc create/edit, cloud-space search** → `lark-doc` (`docs +search` to locate any cloud resource).
- **Spreadsheets** → `lark-sheets`. **Bitable** (multi-dim, formulas) → `lark-base`.
- **Tasks / todos** → `lark-task`. **Wiki** → `lark-wiki`.
- **Email** → `lark-mail`. **Approval** → `lark-approval`. **Attendance** → `lark-attendance`.
- **Meeting minutes** (ended meetings) → `lark-minutes` / `lark-vc`.
- **Whiteboard** (diagrams, flows) → `lark-whiteboard` (DSL / PlantUML / Mermaid).
- **Slides** → `lark-slides`. **Real-time events** → `lark-event`.
- **Composite workflows** → `lark-workflow-meeting-summary`, `lark-workflow-standup-report`.
- **Auth / `Permission denied`** → `lark-shared`.
- **API not covered by any skill** → `lark-openapi-explorer`.

First-time setup: `lark-cli config init` then `lark-cli auth login`.

## 8. Code & Style Conventions

(System prompt already covers comments, docstrings, no backwards-compat shims, no scaffolding for hypothetical needs.)

- **Indentation**: 2 spaces (TS / JS / JSON / YAML), 4 spaces (Python), tabs (Go).
- **Naming**: `camelCase` for vars and functions, `PascalCase` for types and React components, `SCREAMING_SNAKE_CASE` for env constants.
- **Files**: collocate `Component.tsx` + `Component.test.tsx` + `Component.module.css`.
- **Imports**: `@/...` absolute aliases when relative depth ≥ 2.
- **Errors**: throw typed errors with context. Validate at system boundaries only.

## 9. Git Workflow

(System prompt already enforces: never `--no-verify`, never force-push to `main`, never amend pushed commits, prefer specific files over `git add .`/`-A`, commit only when explicitly asked, HEREDOC for messages with `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer.)

**Branching (GitHub Flow)**:

- Feature branches off `main`. Never commit directly to `main` / `master`.
- Branch names: `<type>/<short-kebab>` — `feat/auth-redirect`, `fix/empty-cart-crash`, `chore/bump-deps`.
- Squash-merge via PR. Rebase only on local unpushed commits.

**Conventional Commits + 50/72**:

- Format: `<type>[scope][!]: <subject>` — imperative, ≤72 chars (target 50), no trailing period.
- Types: `feat` `fix` `docs` `style` `refactor` `perf` `test` `chore` `build` `ci` `revert`.
- Breaking: `feat!: …` *and* a `BREAKING CHANGE: <reason>` footer (uppercase).
- Body wraps at 72 cols; explains *why*, not *what*.
- Spec: [conventionalcommits.org](https://www.conventionalcommits.org/en/v1.0.0/).

**Hooks**: if a hook fails, fix the root cause, re-stage, create a *new* commit (the failed one was never created — don't `--amend`).

**Worktrees** (`superpowers:using-git-worktrees`):

- Use for parallel feature work, plan execution, or risky experiments.
- After `git worktree add`: copy `.env*` files manually (gitignored, don't carry over). Re-run `pnpm install` if `node_modules` is missing.
- Cleanup: `rtk git worktree remove <path>`. **On Windows, close all editors / terminals inside the worktree first** — open file handles cause removal to fail.
- Periodic: `rtk git worktree prune`; `commit-commands:clean_gone` removes local branches whose remote is gone.

**GitHub PRs**:

- Link issues with `Fixes #N` / `Closes #N` — auto-closes on merge.
- WIP: `--draft`. Self-assign with `--assignee @me` when solo.
- Read review comments: `rtk gh api repos/<owner>/<repo>/pulls/<n>/comments`.

**Signing**: honor whatever the user / project configured (GPG, SSH, or none). Never `--no-gpg-sign`.

## 10. Verification Before Done

Never claim "done" / "fixed" / "passing" without running checks. Pick what applies:

- Unit tests → `rtk vitest run` / `rtk cargo test`
- E2E → `rtk playwright test`
- Types → `rtk tsc` (clean)
- Lint → `rtk lint` (clean)
- Build → `rtk next build` / `rtk cargo build`
- Git state → `rtk git status` clean
- UI changes → drive `mcp__playwright` to visually verify, or explicitly state "I cannot verify the UI from here"

Show command output, not summaries of it.

## 11. Memory & Recall

- **Auto-memory** (`~/.claude/memory/`) captures session learnings — let it work; don't duplicate here.
- **`episodic-memory:search-conversations`** — recall how something was solved before. Use *before* declaring "I don't know how to approach this."
- **`mcp__memory`** — persistent knowledge graph for cross-project entities and relations.
- **CLAUDE.md** = stable rules only. Project-specific knowledge → project-level `CLAUDE.md`.
- **Verify-before-trust**: a memory naming a file / function / flag is a *historical claim*. Confirm it still exists (Read / Grep) before acting on it.

## 12. Prompt Optimization

(System prompt already covers: brief subagents like a smart colleague who just walked into the room; never delegate understanding; put parallel Agent calls in one tool-use block.)

**`project-prompt-optimizer` skill** — invoke when:

- User gave a vague execution request ("fix the bug", "improve this module").
- A prompt will be reused (cron, `/loop`, repeated dispatch).
- The repo has heavy conventions (custom test runners, CI gates) a generic prompt would miss.

**Subagent vs inline**:

- ✅ Open-ended cross-codebase questions, 2+ independent tasks, work whose raw output would pollute main context.
- ❌ Tasks completable in 1–2 tool calls — delegation overhead exceeds benefit.

**Self-prompts** (`TaskCreate`, `ScheduleWakeup`, `CronCreate`):

- Treat as subagent prompts — future-you has no context either.
- Specify task, intent, constraints, and the *signal* to watch for.
- `ScheduleWakeup`: prompt-cache TTL is 5 min. Pick `delaySeconds` of **270** (warm) or **≥1200** (commit to cold restart). Avoid 300 — worst of both.

**Ask vs assume** (`AskUserQuestion`):

- Ask when requirements are unclear, multiple valid approaches exist, or load-bearing assumptions need verification. ≤4 questions × 2–4 options.
- Don't ask for trivial scope (typo, rename, log line).

**Prompt anti-patterns**:

- ❌ Vague verbs — "optimize", "make it better". Rewrite as: *symptom + likely location + definition of fixed*.
- ❌ Missing context — error text, file paths, what already failed.
- ❌ Prescribed step-by-step procedure where the premise might be wrong.
- ❌ "Based on your findings, do X" — that's delegation of understanding.

## 13. Setup-Specific Anti-patterns

(System prompt already prohibits: destructive git ops without authorization, `--no-verify`, force-push to main, amending pushed commits, `git add .`/`-A`, committing without explicit request, multi-paragraph docstrings, creating planning `.md` files unsolicited, `find`/`grep`/`cat`/`sed`/`head`/`tail` via Bash instead of dedicated tools.)

This setup adds:

- ❌ Running shell commands without `rtk` prefix.
- ❌ Re-deriving library APIs from training data when `mcp__context7` could fetch fresh docs.
- ❌ Hand-rolling Feishu API calls when a `lark-*` skill exists (§7).
- ❌ Hand-writing a UI component when `mcp__shadcn` ships it.
- ❌ Bash idioms on a PowerShell host — `/dev/null` instead of `$null`, `$VAR` instead of `$env:VAR`.
- ❌ Locale mismatch — replying in English when the user wrote Chinese (and vice versa).
- ❌ Enumerating every available skill or MCP — they self-describe via metadata. Reference by purpose.

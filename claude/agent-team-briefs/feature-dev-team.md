# Feature Dev Team — paste-in spawn brief

Use when delivering a Next.js + React Native end-to-end feature. Lead = your current Claude Code session.

## Prerequisites

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `~/.claude/settings.json` env (already set)
- Subagent definitions present in `~/.claude/agents/`: nextjs-developer, expo-react-native-expert, test-automator, debugger
- On Windows / VS Code / Windows Terminal, prefer `--teammate-mode in-process` when launching the lead session

## Paste-in prompt

```
Spawn an agent team of 4 teammates to deliver feature: <FEATURE_NAME>.

Goal: <one-line outcome — e.g., "Add an organization invite flow that works on web and mobile, gated by RBAC.">

Teammates and ownership:
1. planner — uses the writing-plans superpower. Owns docs/plans/<feature>.md.
   Must produce the plan and get my (lead) explicit approval before any teammate writes code.
2. web-impl — uses subagent type `nextjs-developer`. Owns app/, components/, lib/ on web.
   Must not touch mobile/ or any test file.
3. mobile-impl — uses subagent type `expo-react-native-expert`. Owns mobile/, screens/, native modules.
   Must not touch app/ or any web file.
4. qa — uses subagent type `test-automator`. Owns tests/ (Vitest), e2e/ (Playwright), and any *.test.tsx
   colocated next to source. Must not modify implementation files; only tests.

Gates:
- planner approval gate before web-impl and mobile-impl start
- web-impl and mobile-impl run in parallel after the gate (independent file scopes)
- qa runs last, blocking final integration; failures route back to whichever impl owns the file

Verification:
- qa must run `rtk vitest run` and `rtk playwright test` before declaring done
- web-impl must run `rtk tsc --noEmit` and `rtk next build`
- mobile-impl must run `rtk tsc --noEmit` and the appropriate Expo prebuild check

Coordination rules:
- No two teammates may edit the same file. Conflict = page lead (me) for arbitration.
- All teammates write progress notes to docs/plans/<feature>-progress.md.
- Each teammate must read docs/plans/<feature>.md before any tool call.

Begin by spawning the planner only. Hold the others until I approve the plan.
```

## Notes

- 4 teammates fits the recommended 3–5 range. Add a fifth (e.g. `docs-writer`) only if the feature has user-facing copy that needs i18n + changelog.
- `planner` is a built-in superpower (writing-plans skill), not a subagent file — that's intentional, planning skills are richer than a pure subagent system prompt.
- If the feature is web-only, drop `mobile-impl`. If it's pure refactor, swap `web-impl` for `refactoring-specialist`.

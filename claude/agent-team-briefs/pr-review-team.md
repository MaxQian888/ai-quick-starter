# PR Review Team — paste-in spawn brief

Use to get parallel security + performance + accessibility review on a PR or local diff. Lead = your current Claude Code session, holding the merged-view of all findings.

## Prerequisites

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Subagent definitions: security-auditor, performance-engineer, accessibility-tester
- Read-only review: each teammate writes findings, never source files

## Paste-in prompt

```
Spawn a 3-teammate review team for PR #<N> (or current branch diff if no PR yet).

Teammates:
1. sec — subagent type `security-auditor`. Reviews diff for OWASP Top 10, secret leakage,
   auth/authz regressions, dependency CVEs. Writes findings to reviews/<pr>-security.md.
2. perf — subagent type `performance-engineer`. Reviews diff for bundle-size delta,
   render-blocking work, RSC/CSR boundary regressions, Core Web Vitals impact.
   Writes findings to reviews/<pr>-perf.md.
3. a11y — subagent type `accessibility-tester`. Reviews diff for WCAG 2.2 AA, ARIA,
   keyboard navigation, focus management, color contrast. Writes findings to
   reviews/<pr>-a11y.md.

Constraints:
- All three teammates run in parallel — they read the same diff and never touch source.
- Each writes ONLY to its assigned reviews/*.md path. Never edit source.
- Each finding includes: severity (blocker/major/minor/nit), file:line, evidence, suggested fix.
- No teammate may say "looks good" without listing what they actually checked.

After all three complete, I (lead) will:
- Read the three reviews/*.md files
- Synthesize a single PR comment using the code-review skill
- Post via `rtk gh pr review` if requested

Begin by spawning all 3 in parallel.
```

## Notes

- This is the most effective use of agent teams — three concurrent read-only roles produce ~3x faster review than serial.
- Add a fourth teammate (`reviewer` using superpowers code-reviewer) when the diff is large (>500 lines) and a generalist sweep is needed.
- For high-stakes PRs (auth, payment, migration), upgrade `sec` model to `opus` per-session via `--model opus`.

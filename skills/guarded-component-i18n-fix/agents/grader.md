# Grader

## Purpose

Evaluate whether the agent correctly detected the repository's existing i18n stack before making any changes, respected confidence levels, and only modified files in the safe-fix plan.

## Scoring Criteria

1. **Stack Detection** (30%): Did the agent run the audit script and check `selected_system.confidence` before editing?
2. **Guardrail Respect** (30%): Did the agent avoid introducing a second framework, new providers, or bulk rewrites?
3. **Minimal Fix** (20%): Were only files in `safe_fix_plan` modified, using existing conventions?
4. **Verification** (20%): Did the agent verify against an existing localized component or test stack?

## Pass Threshold

Score >= 75% to pass. Introducing a duplicate i18n framework is an automatic critical failure.

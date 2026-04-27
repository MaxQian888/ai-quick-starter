# Grader

## Purpose

Evaluate whether the agent correctly inspected existing workflows, chose the appropriate mode, ran orchestration for broad work, and applied governance guardrails when editing CI files.

## Scoring Criteria

1. **Inspection** (20%): Did the agent read existing `.github/workflows/` and manifests before planning?
2. **Mode Selection** (20%): Was the narrowest appropriate mode chosen (version check, split plan, local sim, or full orchestration)?
3. **Live Verification** (25%): Did the agent re-run live verification after editing `uses:` references?
4. **Governance** (20%): Were permissions kept narrow, SHA pinning applied, and concurrency rules respected?
5. **Scope Honesty** (15%): Did the agent separate findings, proposed files, and local verification scope honestly?

## Pass Threshold

Score >= 75% to pass.

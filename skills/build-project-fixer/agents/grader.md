# Grader

## Purpose

Evaluate whether the agent correctly discovered repository build commands, reproduced the smallest failing path, applied a minimal valid fix, and widened verification without weakening checks.

## Scoring Criteria

1. **Discovery** (25%): Did the agent run the discovery script and read its output before attempting fixes?
2. **Narrow Reproduction** (25%): Did the agent reproduce the specific failing command rather than guessing?
3. **Minimal Fix** (25%): Was the applied fix the smallest valid repair, without deleting tests or weakening rules?
4. **Verification** (25%): Did the agent re-run the failing command and then broader verification before claiming success?

## Pass Threshold

Score >= 75% to pass. Any score below 50% is a critical failure.

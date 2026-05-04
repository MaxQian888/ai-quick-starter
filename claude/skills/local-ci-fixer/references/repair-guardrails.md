# Repair Guardrails

Allowed fixes:
- targeted code changes,
- supported configuration fixes,
- missing local test or lint prerequisites inside the repository,
- small script corrections that align local behavior with the intended CI checks.

Forbidden shortcuts:
- deleting tests,
- lowering coverage thresholds,
- weakening lint or typecheck rules,
- editing workflow files only to simplify local execution,
- claiming full CI success when only a subset ran locally.

Repair loop:
1. capture the first failing command or step,
2. fix the root cause,
3. re-run that failing scope,
4. re-run the broader local CI path,
5. stop and report if the remaining blocker is environmental or remote-only.

Preserve unrelated user changes and keep the scope as narrow as possible.

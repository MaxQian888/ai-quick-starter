# Repair Guardrails

Allowed fixes:
- targeted code fixes,
- supported repository configuration fixes,
- lockfile refreshes,
- narrow dependency upgrades backed by failure evidence,
- script corrections that restore intended build or validation behavior.

Dependency upgrade rules:
- Upgrade only the package or lockfile scope implicated by the failure.
- Prefer the smallest version movement that resolves the incompatibility.
- Re-run the failing command immediately after the upgrade.
- If the first upgrade attempt still fails for the same reason, stop after a small number of targeted attempts and report what changed.

Forbidden shortcuts:
- deleting tests,
- lowering coverage thresholds,
- weakening lint or typecheck rules,
- disabling build steps,
- commenting out intended logic to hide a failure,
- mass dependency churn without evidence,
- editing CI only to avoid reproducing the real failure locally.

Preserve functionality:
- Keep unrelated user changes intact.
- Prefer fixes that align with existing repository patterns.
- If a repair would change user-visible behavior, state the tradeoff instead of hiding it.

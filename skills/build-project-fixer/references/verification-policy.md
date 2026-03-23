# Verification Policy

Use narrow-to-broad verification:

1. Re-run the exact failing command.
2. If it passes, run the next broader command in the same area.
3. If that passes, run the main build or verify command that best represents repository health.

Verification rules:
- Do not claim the issue is fixed until the original failing command passes.
- Do not claim the repository is clean unless the broader verification path also passes.
- If only part of the command surface was verified, say exactly which commands passed and which were not run.

Environmental blockers:
- missing system tools,
- unavailable services or secrets,
- platform-specific behavior that cannot be reproduced locally,
- incomplete repository setup.

When blocked:
- report the command that was attempted,
- report the exact blocker,
- separate environmental blockers from repository defects,
- state the highest-confidence next command if the blocker is removed.

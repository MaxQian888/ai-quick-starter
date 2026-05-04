# Execution Policy

Use `scripts/local_ci_gate.py` before deciding how to run anything.

Prefer `act` when:
- `selected_mode` is `act`,
- Docker is available,
- the workflow is not deploy-only,
- no missing secret or hosted-service dependency blocks useful local verification.

Prefer fallback mode when:
- `act` or Docker is unavailable,
- the useful part of the workflow is mainly `run:` steps,
- partial local verification is still valuable.

Stop and ask for approval before:
- installing `act`, Docker, or language toolchains,
- running commands that would publish, deploy, or mutate external systems,
- injecting secrets into local execution.

If the workflow is deployment-heavy or secret-dependent, report a partial or blocked result instead of forcing execution.

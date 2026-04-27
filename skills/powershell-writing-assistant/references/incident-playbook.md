# Incident Playbook

## Trigger Conditions

Start this playbook when any of the following occurs:

- Script execution fails in production or scheduled jobs.
- CI workflow fails after script/module changes.
- Script behavior causes unexpected mutation or data risk.
- Security-sensitive operation runs outside intended scope.

## Severity Triage

Classify quickly before deep analysis:

- Sev-1: Ongoing outage, data loss risk, or security exposure.
- Sev-2: Major function degradation with workaround.
- Sev-3: Localized failure with low business impact.

Record incident start time, impacted command/module, environment, and operator.

## Immediate Containment

- Stop automated triggers for the failing script when safe.
- Disable destructive code path by feature flag or guarded switch.
- Force read-only mode where possible.
- Preserve logs and artifacts before cleanup.

Do not continue blind retries when side effects are possible.

## Fast Diagnosis Checklist

1. Confirm exact command line and parameter set used.
2. Confirm runtime (`$PSVersionTable.PSVersion`) and host context (local/CI/runner).
3. Reproduce with minimal input in an isolated environment.
4. Inspect parser/lint/test outputs first:
   `scripts/invoke-pwsh-quality-gate.ps1 -Path . -Recurse`
5. Check native command exit codes and external dependency status.
6. Validate secrets/config source and token expiration.

## Rollback Criteria

Rollback immediately when:

- Mutation path is incorrect and no safe hotfix is validated.
- Incident is Sev-1 and blast radius is expanding.
- Fix confidence is low or verification coverage is insufficient.

Preferred rollback order:

1. Revert to last known good script/module version.
2. Re-run smoke checks and critical Pester tests.
3. Re-enable automation gradually after validation.

## Recovery Verification

Before closing incident:

- Confirm core command path succeeds on representative inputs.
- Confirm no unexpected side effects remain.
- Confirm CI quality gate and tests pass.
- Confirm monitoring/alerts return to normal baseline.

## Post-Incident Hardening

- Add or update Pester coverage for the failed scenario.
- Add guardrails (`ShouldProcess`, input validation, timeout, retries).
- Update `references/common-task-recipes.md` or related references if pattern gaps were found.
- Document root cause and concrete prevention actions.

## Incident Note Template

Use this minimal structure:

- Incident ID:
- Severity:
- Start/End time (UTC):
- Impact summary:
- Triggering change:
- Root cause:
- Containment actions:
- Rollback/fix details:
- Verification evidence:
- Follow-up tasks and owner:

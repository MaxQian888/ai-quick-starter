# External Skill Notes

## Local Repository Pattern

This skill follows the authored-skill pattern used across this repository:

- concise `SKILL.md`
- UI metadata in `agents/openai.yaml`
- focused `references/`
- optional helper automation in `scripts/`
- optional contract tests in `tests/`

That pattern is visible in modules such as `build-project-fixer` and `codebase-indexing-assistant`.

## Why This Skill Is Config-Centric

Public skill packs already split Kubernetes work into narrower specialties. For example, the `foxj77/claude-code-skills` collection separates Helm chart development, namespace troubleshooting, security hardening, and broader platform operations into different skills.

This repository does better with narrower authored modules, so this skill intentionally focuses on:

- kubeconfig and context selection
- manifest ownership and edit boundaries
- Helm values versus template edits
- Kustomize base and overlay decisions
- ConfigMap, Secret, resource, and RBAC safety checks

It does not try to become a full cluster-operations, GitOps, or incident-response pack.

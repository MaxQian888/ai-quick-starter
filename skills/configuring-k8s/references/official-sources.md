# Official Sources

Read these primary sources when the related topic appears. This skill is intentionally anchored to official docs instead of blog-post folklore.

## Kubernetes

- Kubeconfig and context management:
  - https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/
- Resource requests and limits:
  - https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- RBAC good practices:
  - https://kubernetes.io/docs/concepts/security/rbac-good-practices/
- Secret handling guidance:
  - https://kubernetes.io/docs/concepts/security/secrets-good-practices
- Kustomize with `kubectl`:
  - https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/

## Helm

- Values file design:
  - https://helm.sh/docs/chart_best_practices/values/
- Template structure and naming:
  - https://helm.sh/docs/chart_best_practices/templates/

## What This Skill Pulls From Those Sources

- kubeconfig files organize clusters, users, and namespaces, and Windows uses `;` in `KUBECONFIG`
- requests guide scheduling, limits guide enforcement, and memory pressure can cause `OOMKilled`
- RBAC should stay namespace-scoped and least-privileged whenever possible
- Secrets are not safely protected by base64 alone
- Helm values should stay easy to override and templates should stay namespaced and predictable
- Kustomize should compose bases and overlays rather than duplicating manifests

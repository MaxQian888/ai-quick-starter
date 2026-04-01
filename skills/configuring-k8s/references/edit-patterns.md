# Edit Patterns

Use these patterns when the user asks for a concrete K8s config change and the owning layer is already known.

## Add Environment Configuration

Question to answer first:
- non-sensitive config or sensitive credential?

Pattern:
- non-sensitive: `ConfigMap`
- sensitive: `Secret`
- wire the value through `env`, `envFrom`, or a volume mount
- do not inline secrets directly into workload manifests unless the repository already uses encrypted secret tooling and the committed file is expected to stay encrypted

## Add or Tune Probes

Prefer:
- `startupProbe` when the app has a slow boot path
- `readinessProbe` for traffic gating
- `livenessProbe` for deadlock or unrecoverable stuck-state recovery

Check:
- path and port match the container
- probe timing reflects actual startup and steady-state behavior
- Helm or Kustomize already exposes the probe shape before editing lower layers

## Tune Requests and Limits

Change the narrowest owning file first:
- Helm: `values*.yaml`
- Kustomize: patch or overlay
- raw manifest: workload file

Keep explicit:
- `requests.cpu`
- `requests.memory`
- `limits.cpu`
- `limits.memory`

Remember:
- CPU limit throttles
- memory limit can lead to `OOMKilled`

## Add Network Exposure

When exposing an app:
- confirm whether the repository uses `Service`, `Ingress`, gateway APIs, or chart-level exposure flags
- keep selectors aligned with pod-template labels
- prefer updating an existing service or ingress path over creating a parallel object with overlapping selectors

## Helm vs Kustomize vs Raw Manifest

Choose in this order:

1. Helm values if the chart already exposes the knob
2. Kustomize patch or overlay if the repository customizes a base per environment
3. chart template edit only when the chart is missing the capability
4. raw manifest edit only when no higher-level abstraction owns the object

## RBAC Change

Default to:
- `Role`
- `RoleBinding`
- namespace scope

Escalate only with evidence:
- `ClusterRole`
- `ClusterRoleBinding`
- wildcard resources or verbs

Check whether the user is really asking for access to create workloads, list secrets, mint service-account tokens, or other privilege-escalating actions.

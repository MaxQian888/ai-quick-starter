# Configuration Playbook

## Reading Order

Use this order unless the user already named the owning file:

1. discovery script output
2. cluster access or kubeconfig files
3. top-level chart or kustomization entrypoint
4. environment values or overlay files
5. workload and network manifests
6. RBAC and secret-bearing objects

## 1. Cluster Access and Context

- Confirm whether the task is about access, repository config, or both.
- Inspect `kubectl config view` and the active context before changing manifests.
- On Windows, `KUBECONFIG` uses `;` as the file-list delimiter.
- Treat kubeconfig files like executable inputs. Do not trust them blindly.

Read the official kubeconfig doc first when the task mentions:
- multiple clusters
- switching users or namespaces
- a kubeconfig merge
- `KUBECONFIG`

## 2. Raw Manifest Checklist

For Deployments, StatefulSets, DaemonSets, Jobs, CronJobs, Services, and Ingress:

- keep `metadata.labels`, selectors, and pod-template labels aligned
- preserve namespace intent instead of silently moving objects to `default`
- make `resources.requests` and `resources.limits` explicit when the workload is not intentionally burst-only
- keep probes and ports consistent with the container image and exposed service
- separate config from secrets

Resource notes from official docs:

- CPU limits are enforced by throttling.
- Memory limits are enforced reactively and can lead to `OOMKilled`.
- If a limit exists but no request is set, Kubernetes may copy the limit into the request.

## 3. Helm Path

Prefer Helm when the repository already owns the resource through:
- `Chart.yaml`
- `values*.yaml`
- `templates/*.yaml`
- `helmfile.yaml`

Work in this order:

1. inspect `values.yaml` and environment-specific values files
2. change values first if the chart already supports the desired knob
3. edit templates only when the chart structure itself is missing the needed behavior
4. render with `helm template`
5. lint if the chart is meant to be packaged or shared

Helm best-practice reminders:

- keep value keys lowercase camelCase
- favor flatter values unless a related group truly belongs together
- document each public value in `values.yaml`
- use dashed template filenames and one resource per template file
- namespace defined templates such as `mychart.fullname`

## 4. Kustomize Path

Prefer Kustomize when the repository owns the resource through:
- `kustomization.yaml`
- base and overlay directories
- patch files
- `configMapGenerator` or `secretGenerator`

Work in this order:

1. identify the base and the overlay that actually owns the target environment
2. keep cross-cutting namespace, labels, annotations, and name prefixes in the kustomization layer
3. prefer small single-purpose patches
4. use generators for derived ConfigMaps or Secrets when the repo already follows that pattern
5. preview with `kubectl kustomize` and `kubectl diff -k`

Kustomize reminders from official docs:

- `kubectl apply -k` is the apply path
- `kubectl kustomize <dir>` previews rendered resources
- bases and overlays are for composition, not duplication
- generator hashes exist for rollout safety unless intentionally disabled

## 5. ConfigMaps, Secrets, and RBAC

ConfigMaps:
- use for non-sensitive configuration
- keep application config separate from workload structure when possible

Secrets:
- use for sensitive data only
- base64 is encoding, not encryption
- do not commit cleartext or trivially recoverable secret values
- avoid broad `get`, `list`, or `watch` access

RBAC:
- prefer `Role` plus `RoleBinding` at namespace scope
- avoid `cluster-admin`, wildcards, and broad `ClusterRoleBinding` unless the task explicitly requires them
- treat `list` or `watch` on Secrets as sensitive access
- remember that creating workloads can implicitly expose mounted Secrets and service-account permissions

## 6. Verification Ladder

Use the narrowest verification that matches the owning config layer:

- kubeconfig: `kubectl config view`, `kubectl config current-context`
- raw manifest: `kubectl diff -f`, then `kubectl apply --dry-run=server -f` when available
- Helm: `helm template`, optionally `helm lint`
- Kustomize: `kubectl kustomize`, then `kubectl diff -k`

If the repository owns multiple environments:
- verify the exact environment file or overlay you changed
- state what was not rendered or diffed

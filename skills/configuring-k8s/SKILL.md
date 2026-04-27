---
name: configuring-k8s
description: >
  Make sure to use this skill whenever the user needs to inspect, edit, or
  validate Kubernetes configuration in a repository, including raw manifests,
  Helm charts, Helmfile releases, or Kustomize overlays. Also trigger for
  cluster context switching, namespace changes, ConfigMap or Secret updates,
  Service/Ingress modifications, RBAC changes, resource limit adjustments,
  probe configuration, or "help me with my k8s yaml." Covers synonyms like
  "Kubernetes config," "K8s manifests," "Helm values," "Kustomize patches,"
  "deployment yaml," "cluster configuration," and "container orchestration
  setup." Use it even when the user only mentions "my k8s setup" or
  "help me deploy this to Kubernetes."
---

# Configuring K8s

Discover the repository's Kubernetes configuration surface before editing YAML. Pick the narrowest configuration layer that owns the change, then verify with rendering or diff commands before claiming the update is safe.

## Adaptive Detection

Before editing, detect the configuration landscape:

- Identify the primary toolchain: raw manifests, Helm, Kustomize, Helmfile, or mixed.
- Check for kubeconfig files and active cluster context.
- Detect chart structure: `Chart.yaml`, `values*.yaml`, `templates/`.
- Detect Kustomize structure: `kustomization.yaml`, bases, overlays, patches.
- Check for existing namespaces, resource limits, probes, and RBAC rules.
- Identify the target environment: dev, staging, or production.

## Workflow

1. Confirm the repository root plus the target environment, namespace, and cluster context.
2. Run the discovery helper before opening many YAML files:

```bash
python scripts/discover_k8s_surface.py --project-root <repo> --json
```

3. Read these fields first:
   - `toolchains`
   - `entrypoints`
   - `files`
   - `suggested_read_order`
   - `risks`
4. Choose one primary edit path:
   - `kubeconfig` or cluster-access issue: inspect the active context and namespace before editing workloads.
   - raw manifests: edit the smallest manifest set that owns the workload or service.
   - Helm: prefer `values*.yaml` changes before editing chart templates.
   - Kustomize: decide whether the change belongs in a base, overlay, generator, or patch.
5. Apply the smallest valid change and keep secrets, RBAC, selectors, labels, and resource settings explicit.
6. Re-render or diff before broader verification.

## Command Shapes

Discover the config surface:

```bash
python scripts/discover_k8s_surface.py --project-root <repo> --json
```

Inspect the active kubeconfig view:

```bash
kubectl config view
```

Render Helm output without applying:

```bash
helm template <release> <chart-dir> -f <values-file>
```

Preview Kustomize output:

```bash
kubectl kustomize <overlay-dir>
```

Diff raw or rendered resources:

```bash
kubectl diff -f <manifest>
kubectl diff -k <overlay-dir>
```

## Decision Rules

- Prefer repository source files over editing rendered output.
- Prefer `values*.yaml` over chart template changes when Helm already exposes the knob you need.
- Prefer a small Kustomize patch over copying a full base into an overlay.
- Keep `ConfigMap` for non-sensitive config and `Secret` for sensitive data.
- Treat RBAC edits as security changes. Default to namespace scope and least privilege.
- If a repository mixes Helm and Kustomize, preserve the existing ownership boundary instead of cross-wiring both.

## Common Mistakes

- Editing rendered YAML instead of the owning `values.yaml`, template, base, or overlay.
- Treating every manifest under a Kustomize tree as a separate toolchain instead of part of the same ownership boundary.
- Using `Secret` and `ConfigMap` interchangeably.
- Relaxing RBAC or removing probes and limits to bypass a rollout problem.
- Trusting a new kubeconfig file without inspection.

## Guardrails

- Do not use kubeconfig files from untrusted sources without inspection.
- Do not check secret values into manifests, comments, examples, or logs.
- Do not widen selectors, ports, RBAC verbs, or namespaces casually.
- Do not remove requests, limits, probes, or labels just to make a deployment "work".
- Do not claim a configuration is safe if you only edited files and never rendered or diffed the result.

## Examples

**Discover K8s surface in a repo:**
```bash
python scripts/discover_k8s_surface.py --project-root . --json
```

**Preview Helm changes before applying:**
```bash
helm template my-release ./charts/my-app -f ./values-staging.yaml
kubectl diff -f ./rendered.yaml
```

## References

- Read [references/configuration-playbook.md](references/configuration-playbook.md) for the end-to-end workflow and edit checklists.
- Read [references/edit-patterns.md](references/edit-patterns.md) for concrete change-shape examples such as probes, env vars, resources, and Helm-vs-Kustomize ownership decisions.
- Read [references/output-schema.md](references/output-schema.md) for the discovery script contract.
- Read [references/official-sources.md](references/official-sources.md) for the official Kubernetes, Helm, and Kustomize sources this skill is anchored on.
- Read [references/external-skill-notes.md](references/external-skill-notes.md) for the authored-skill patterns and the scope choice relative to broader K8s skill packs.

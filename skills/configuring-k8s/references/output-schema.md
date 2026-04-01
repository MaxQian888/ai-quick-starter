# Output Schema

## JSON Fields

### Top Level

- `project_root`: absolute repository root that was scanned
- `toolchains`: detected configuration systems such as `raw-manifest`, `helm`, `kustomize`, `kubeconfig`, or `helmfile`
- `entrypoints`: high-signal files or directories that likely own configuration changes
- `files`: per-file records for relevant Kubernetes configuration files
- `suggested_read_order`: recommended first files to inspect
- `risks`: important caveats before editing

### `toolchains[]`

- `name`: detected toolchain
- `evidence`: short list of paths or reasons

### `entrypoints[]`

- `path`: repository-relative path
- `kind`: entrypoint category such as `chart`, `kustomization`, `values`, `kubeconfig`, or `manifest`
- `reason`: why the file is a strong starting point

### `files[]`

- `path`: repository-relative path
- `type`: normalized record type such as `helm-chart`, `helm-values`, `helm-template`, `kustomization`, `kubeconfig`, or `manifest`
- `toolchain`: owning configuration system
- `kind`: Kubernetes resource kind when cheaply detectable
- `api_version`: Kubernetes API version when cheaply detectable
- `name`: metadata name when cheaply detectable
- `namespace`: metadata namespace when cheaply detectable
- `templated`: whether the file appears to contain template markers
- `reason`: short explanation for why the file matters

### `risks[]`

- human-readable warnings such as:
  - mixed toolchains
  - secret-bearing manifests
  - templated files that require render steps
  - no clear entrypoint detected

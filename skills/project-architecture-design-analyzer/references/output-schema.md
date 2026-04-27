# Output Schema

## Markdown Sections

The rendered report should contain these sections in order:

1. `Request`
2. `Repository Snapshot`
3. `Architecture Shape`
4. `Design Signals`
5. `Drift Risks`
6. `Linked Skills`
7. `Suggested Next Reads`
8. `Limits`

## JSON Top-Level Fields

```json
{
  "repo_root": "string",
  "request": {},
  "summary": {},
  "files": [],
  "architecture": {},
  "linked_skills": [],
  "suggested_next_reads": [],
  "limits": []
}
```

## `request`

- `focus`: optional user-supplied architecture concern.
- `includes`: relative prefixes explicitly included.
- `excludes`: relative prefixes explicitly excluded.
- `max_files`: scan cap used for the run.
- `depth`: directory-summary depth.

## `summary`

- `total_files`: number of scanned files.
- `languages[]`: language counts from file suffixes.
- `docs[]`: promoted documentation paths.
- `manifests[]`: detected manifest paths.
- `commands[]`: command hints extracted from manifests or task runners.

## `files[]`

Each file record should include:

- `path`
- `language`
- `roles`
- `imports`
- `symbols`
- `reason`
- `resolved_imports`

`resolved_imports` is still heuristic. It reflects the best local static match, not semantic proof.

## `architecture`

### `entry_candidates[]`

- likely bootstrap or top-level surfaces
- include `path`, `reason`, `confidence`, and `score`

### `top_directories[]`

- grouped ownership buckets
- include `path`, `file_count`, and `dominant_roles`

### `boundaries[]`

- observed cross-directory handoffs from static imports
- include `from`, `to`, `count`, `evidence`, `confidence`, and `reason`

### `design_patterns[]`

- inferred architecture patterns from file shape and boundaries
- include `name`, `summary`, `evidence`, and `confidence`

### `drift_risks[]`

- heuristic risk prompts such as missing docs, mixed runtimes, or thin tests
- include `kind`, `summary`, `evidence`, and `confidence`

## `linked_skills[]`

Each recommendation should include:

- `skill`
- `reason`
- `when_to_use`

These are next-step options, not mandatory workflow jumps.

## `suggested_next_reads[]`

- the smallest follow-up file set worth opening next
- include `path` and `reason`

## `limits[]`

Use this to record scan truncation or similar constraints.

Example:

```json
{
  "kind": "max-files",
  "detail": "Scan stopped after 200 matching files."
}
```

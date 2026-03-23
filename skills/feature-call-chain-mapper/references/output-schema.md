# Output Schema

## Markdown Sections

The generated Markdown report contains these sections in this order:

1. `Request`
2. `Scope`
3. `Candidate Entrypoints`
4. `Evidence Files`
5. `Symbols`
6. `Call Chain`
7. `Cross-Module Handoffs`
8. `Blind Spots`
9. `Suggested Next Reads`

`Limits` is optional and appears only when the tracer capped or skipped work.

## JSON Fields

### Top Level

- `generated_at`: ISO-8601 timestamp
- `repo_root`: absolute repository root
- `request`: requested feature and explicit anchors
- `scope`: scan filters, caps, and language counts
- `candidate_entrypoints`: promoted starting files
- `evidence_files`: files that support the reported chain
- `symbols`: compact symbol summary for promoted nodes
- `nodes`: detailed node records
- `edges`: structured relationships between nodes
- `cross_module_handoffs`: file-boundary transitions derived from `edges`
- `blind_spots`: required uncertainty notes
- `suggested_next_reads`: follow-up files to inspect manually
- `limits`: scan caps or skipped-work notes

### `request`

- `feature`: raw feature string
- `entry_file`: explicit repository-relative anchor file if provided
- `entry_symbol`: explicit symbol anchor if provided

### `scope`

- `includes`: normalized include prefixes
- `excludes`: normalized exclude prefixes
- `max_files`: scan cap
- `max_depth`: graph expansion cap
- `scanned_files`: number of matching files read
- `languages`: list of `{language, count}` objects

### `candidate_entrypoints[]`

- `path`: repository-relative path
- `language`: detected language
- `reason`: why this file was promoted
- `confidence`: `high` or `medium`

### `evidence_files[]`

- `path`: repository-relative path
- `language`: detected language
- `matched_terms`: feature terms that matched path or text
- `symbol_count`: extracted symbol count
- `confidence`: file-level evidence confidence
- `reason`: promotion reason

### `nodes[]`

- `id`: stable node identifier within this report
- `kind`: symbol kind such as `function` or `class`
- `symbol`: symbol name
- `file`: repository-relative file path
- `line`: 1-based line number
- `language`: detected language
- `role`: semantic role such as `entry` or `implementation`
- `evidence`: `observed` or `inferred`
- `confidence`: `high`, `medium`, or `low`
- `notes`: short explanation

### `edges[]`

- `from`: source node id
- `to`: target node id
- `relation`: relationship label such as `calls` or `references`
- `evidence`: `observed` or `inferred`
- `confidence`: `high`, `medium`, or `low`
- `reason`: short explanation

### `cross_module_handoffs[]`

- `from_file`
- `from_symbol`
- `to_file`
- `to_symbol`
- `relation`
- `confidence`
- `reason`

### `blind_spots[]`

Each item is a plain-language sentence describing uncertainty or a likely missing edge source.

### `suggested_next_reads[]`

- `path`: repository-relative path
- `reason`: why to open this file next

### `limits[]`

- `kind`: machine-friendly limit label
- `detail`: human-readable explanation

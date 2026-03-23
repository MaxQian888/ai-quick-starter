# Output Schema

## Markdown Sections

The generated Markdown report contains these sections:

1. `Repository Overview`
2. `Structure Summary`
3. `Likely Entrypoints and Key Files`
4. `Module and File Roles`
5. `Dependency Clues`
6. `Suggested Reading Order`
7. `Risks and Blind Spots`

## JSON Fields

### Top Level

- `repo_root`: absolute path of the scanned repository root
- `summary`: high-level counts and onboarding signals
- `directories`: aggregated directory summaries
- `files`: per-file heuristic records
- `commands`: likely developer commands inferred from manifests
- `entry_candidates`: ranked bootstrap candidates
- `reading_order`: suggested first files to inspect
- `limits`: scan caps or uncertainty notes

### `summary`

- `total_files`: number of indexed files after filtering
- `languages`: list of `{language, count}` objects
- `docs`: documentation paths promoted as likely onboarding material
- `manifests`: manifest paths promoted as build or dependency sources

### `directories[]`

- `path`: aggregated directory key up to the requested depth
- `file_count`: number of indexed files in that bucket
- `languages`: top language counts for that bucket

### `files[]`

- `path`: repository-relative path
- `extension`: file extension
- `language`: detected language or `unknown`
- `roles`: heuristic roles such as `entry`, `config`, `api`, `ui`, `docs`, `test`, or `library`
- `imports`: shallow import or dependency clues
- `symbols`: shallow symbol names when cheap to extract
- `importance`: `high`, `medium`, or `low`
- `reason`: short explanation for why the file matters

### `commands[]`

- `command`: likely shell command
- `source`: manifest file that produced the command
- `reason`: why the command was proposed

### `entry_candidates[]` and `reading_order[]`

- `path`: repository-relative path
- `reason`: short human-readable explanation for the promotion

### `limits[]`

- `kind`: machine-friendly limit label such as `max-files`
- `detail`: explanation of what was skipped or capped

# Output Contract

The helper emits four artifacts:

- `build.ps1`
- `debug.ps1`
- `build-debug-bundle.json`
- `build-debug-bundle.md`

## JSON Schema

The JSON bundle contains these top-level fields:

- `project_root`
- `package_managers`
- `selected_commands`
- `optional_checks`
- `assumptions`
- `blockers`
- `generated_files`

## `selected_commands`

`selected_commands` contains:

- `install`
- `build`
- `debug`

Each selected command is either `null` or an object with:

- `command`
- `source`
- `evidence`
- `score`

## `optional_checks`

`optional_checks` is a list of objects. Each object contains:

- `bucket`
- `command`
- `source`
- `evidence`
- `score`

## Markdown Headings

The Markdown bundle uses these sections:

- `## Project Profile`
- `## Selected Commands`
- `## Optional Checks`
- `## Blockers`
- `## Assumptions`
- `## Generated Files`

## Script Expectations

### `build.ps1`

- runs from the repository root,
- optionally runs the selected install command,
- optionally runs selected checks when `-IncludeChecks` is set,
- then runs the selected build command,
- or exits with a clear error when no build command was selected.

### `debug.ps1`

- runs from the repository root,
- optionally runs the selected install command,
- then runs the selected quick-debug command,
- or exits with a clear error when no debug command was selected.

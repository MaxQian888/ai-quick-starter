# Cleanup Rules

Use this file when deciding whether a change should be repaired, kept, or cleaned.

## Classification Table

| Classification | Meaning | Action |
| --- | --- | --- |
| `repair-artifacts` | Active change is structurally stale: missing deltas, blocked artifacts, validation failures, or placeholder-heavy content. | Rebuild the missing artifacts before any archive decision. |
| `active-work` | Active change still reflects ongoing implementation work. | Keep the change active and refresh artifacts as work progresses. |
| `ready-for-verify-or-archive` | Active change artifacts are coherent, tasks are complete, and validation is clean. | Perform final verification, then archive if the implementation truly matches. |
| `safe-cleanup-candidate` | Archived folder is placeholder-only, empty-scaffold noise, or clearly duplicated detritus with no meaningful historical payload. | Clean only after recording what is being removed. |
| `keep-history` | Archived folder still contains meaningful proposal, task, or spec history. | Preserve it. |
| `review` | Evidence is mixed or incomplete. | Pause cleanup and inspect manually. |

## Safe Cleanup Signals

Treat an archived folder as `safe-cleanup-candidate` only when the evidence is explicit:

- only `.openspec.yaml` or a single placeholder `proposal.md` remains
- files contain obvious placeholder markers such as `TODO`, `TBD`, `placeholder`, or `replace me`
- there are no meaningful `specs/**/*.md` delta files
- there is no useful `tasks.md` or design history worth preserving

## Keep-History Signals

Treat an archived folder as `keep-history` when any of these are true:

- it contains real delta specs
- it contains a meaningful `tasks.md` or `design.md` that explains why the change existed
- it records important transitions that are no longer visible in current `openspec/specs/`

## Guardrail

Never delete archive history on the first pass.

Always produce an audit note or cleanup report first, then decide whether the archive folder is truly disposable. When in doubt, classify it as `review` or `keep-history`, not `safe-cleanup-candidate`.

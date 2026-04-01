# Detection Playbook

## Candidate Detection

Treat a file as a low-risk migration candidate only when all of these are true:

- the file is a React component file under the requested target path,
- the file uses a supported native element such as `button`, `input`, `textarea`, or `select`,
- the file does not import and render a local wrapper component for the same surface,
- the file does not contain high-risk overlay or composite patterns,
- the requested target library is built in.

## Block Conditions

Block the file when any of these signals appear:

- local wrapper imports such as `PrimaryButton` from a relative path,
- custom dialog or modal semantics such as `role="dialog"` or `aria-modal="true"`,
- composite overlay props such as `open`, `onClose`, and `children` in the same component,
- business-heavy or state-heavy widgets that would need behavioral judgment instead of a direct JSX swap.

## Audit-Only Conditions

Downgrade to audit-only when:

- the requested target library is unsupported,
- the file contains migration candidates but there is no built-in mapping support,
- the repository is too wrapper-heavy to prove a safe direct replacement.

In audit-only mode:

- keep `safe_fix_plan` empty,
- keep `candidate_mappings` descriptive rather than authoritative,
- explain what blocked automatic edits.

## Reading Order

1. Check `target_library`.
2. Check `mode`.
3. Review `component_findings`.
4. Review `candidate_mappings`.
5. Apply only `safe_fix_plan`.

## Stop Signals

Stop and explain instead of editing when:

- every file is blocked,
- the report contains no `safe-candidate` files,
- the migration would require editing shared design-system wrappers outside the requested target,
- targeted validation is not available and runtime parity would be speculative.

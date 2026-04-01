# Analysis Playbook

## Inputs To Prefer

1. Product or feature specs passed through `--doc`.
2. Target-local `README.md`, `AGENTS.md`, and `CLAUDE.md`.
3. Nearby tests, stories, or fixtures that imply expected behavior.
4. The target file or folder itself.

If the important requirements live in a different directory tree, pass them explicitly instead of assuming auto-discovery will find them.
Ancestor `AGENTS.md` and `CLAUDE.md` are context helpers by default. They should not become primary requirement sources unless the user passes them explicitly.

## Status Meanings

- `missing`: the documentation names a capability, but the audited target does not show convincing source or test signals for it.
- `partial`: the target contains some related terms or files, but the documented behavior still looks incomplete.
- `covered`: the local source surface has enough matching signals that the capability should not be listed as missing without further evidence.
- `uncertain`: the requirement text is too weak, too generic, or too poorly matched to support a confident claim.

Related outputs:

- `guardrail_findings`: negative or safety-oriented rules such as "Do not ..." statements.
- contract metadata: hidden by default and only included when `--include-contract-requirements` is enabled.

## How To Write The Final Answer

Use this order:

1. Missing functionality
2. Detailed requirement checklist
3. Assumptions and blind spots

If the user asks for safety rules or package completeness, add a separate guardrail section after the main feature list. Do not merge it into product functionality.

For each accepted gap, include:

- `title`
- `priority`
- `why it appears missing`
- `evidence`
- `acceptance criteria`
- `open questions`

## When To Read More Files

Read additional implementation files before escalating an item when:

- the report marks it `partial`,
- the requirement is business-critical,
- the target surface is large enough that a keyword miss is plausible,
- or tests suggest a different owner than the scanned file set.

Enable `--include-contract-requirements` only when auditing skill contracts, package shape, metadata completeness, or validation obligations is part of the task.

## What Not To Do

- Do not turn every documented sentence into a backlog item.
- Do not turn metadata such as `display_name:` or `description:` into feature gaps unless the user explicitly wants contract auditing.
- Do not report `covered` items as missing just because there is no direct runtime proof.
- Do not collapse `partial` and `missing` into one bucket.
- Do not claim the script proved a production bug.

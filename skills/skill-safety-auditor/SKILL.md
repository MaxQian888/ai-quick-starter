---
name: skill-safety-auditor
description: |
  Use whenever you need to audit one Codex skill folder for safety and security risks before reuse, publishing, or extension, especially when the skill may contain dangerous commands, hardcoded secrets, over-broad trigger wording, unsafe write behavior, or missing verification guardrails. Make sure to use this skill whenever the user says "audit this skill", "is this safe", "review skill", "safety check", "security review", or "can I publish this" — even for skills that look simple or only contain documentation. Also trigger before sharing a skill with a team, before adding a skill to a public registry, or when a skill has been modified and needs re-validation. Covers script-backed skills, doc-backed skills, and hybrid skill packages.
---

# Skill Safety Auditor

## Overview

Audit one skill folder before trusting it. Run the helper script first, read the JSON report first, and treat the `safe_fix_plan` as the maximum allowed edit surface for the next pass.

## Adaptive Detection

Before auditing, detect the skill type:

1. **Script-backed?** Check for executable scripts in `scripts/` that may run destructive commands.
2. **Doc-backed?** Review `SKILL.md` for over-broad triggers or missing guardrails.
3. **Secrets risk**: Scan for API keys, tokens, passwords, or connection strings.
4. **Write behavior**: Check if the skill instructs file overwrites without verification.
5. **Trigger precision**: Verify the description is specific enough to avoid accidental activation.

Use these signals to focus the audit on the highest-risk areas.

## Workflow

1. Confirm the exact target skill directory.
2. Run the audit helper before drawing conclusions:

```bash
uv run --python 3.11 scripts/audit_skill_safety.py --skill-path <path/to/skill>
```

3. Read the JSON output first. Use the Markdown output for human review.
4. Review `overall_status`, `risk_score`, and the highest-severity findings before touching any files.
5. Restrict follow-up edits to the files and operations listed in `safe_fix_plan`.
6. Treat `blocked_actions` as hard stops until the matching finding is resolved.
7. Re-run the audit after every repair pass. Do not claim the skill is safe from stale output.

## What To Read In The Report

- `overall_status`: whether the pass looks clean, needs review, or is high-risk.
- `risk_score`: the aggregate risk estimate for the current static pass.
- `findings`: the exact file-level issues, evidence, and suggested fixes.
- `safe_fix_plan`: the only changes this audit considers safe to apply next.
- `blocked_actions`: actions that should stay off-limits until findings are fixed.
- `blind_spots`: what static analysis could not prove.

## Guardrails

- Do not auto-fix the target skill during the audit pass.
- Do not execute the target skill's helper scripts just because they exist.
- Do not treat a structurally valid skill as safe without reading the risk findings.
- Do not broaden the edit scope beyond `safe_fix_plan` unless the user explicitly asks for a wider remediation pass.
- Do not suppress ambiguous results. If the report says review is needed, keep the uncertainty visible.

## Decision Rules

- If a finding contains a real-looking secret or a destructive command, treat the skill as blocked for reuse until the issue is removed.
- If the trigger description is broad, narrow it before enabling auto-discovery.
- If the skill is script-backed but has no runnable verification surface, add tests or a `runtime-verification.json` contract before trusting it.
- If the report is clean but the skill still looks high-risk by context, inspect the helper scripts and references manually before reuse.

## Examples

### Example 1: Audit a single skill

```bash
uv run --python 3.11 scripts/audit_skill_safety.py --skill-path ./my-skill
```

### Example 2: Audit with strict scoring

```bash
uv run --python 3.11 scripts/audit_skill_safety.py --skill-path ./my-skill --strict
```

## References

- Read [references/detection-rules.md](references/detection-rules.md) for the risk categories and matching heuristics.
- Read [references/output-contract.md](references/output-contract.md) for the JSON and Markdown fields.
- Read [references/remediation-guidelines.md](references/remediation-guidelines.md) when converting findings into a minimal repair pass.

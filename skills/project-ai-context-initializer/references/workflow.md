# Workflow

## Objective

Preserve the user's required orchestration order:
1. timestamp subagent,
2. architecture subagent,
3. local integration,
4. summary in the main chat.

## Subagent Sequence

### Step 1: Datetime Subagent

Dispatch a minimal subagent whose only output is the current timestamp.

Required result:
- one ISO 8601 timestamp string,
- no extra explanation.

### Step 2: Init Architect Subagent

Dispatch a second subagent with:
- the repository root,
- the project summary,
- the timestamp,
- and the request to draft root and module docs.

The architect should:
1. build an inventory,
2. select high-value modules,
3. read only the files needed to understand those modules,
4. draft docs and a coverage report.

## Codex Adaptation

If the original prompt says to use `Task(...)`, adapt it to Codex-native subagent tools:
- `spawn_agent` to create the subagent,
- `send_input` for follow-up instructions,
- `wait_agent` only when the result is needed on the critical path.

Keep the sequencing identical even if tool names differ.

## Suggested Architect Prompt Shape

Include:
- project summary,
- timestamp,
- repository root,
- inventory phase,
- module-priority phase,
- targeted deep-read phase,
- doc-drafting phase,
- and a request for a coverage report with skipped reasons.

## Optional Inventory Helper

Inside the architect flow, a deterministic inventory snapshot can be generated with:

```bash
python scripts/scan_project_context.py --root <repo>
```

Use the resulting JSON to ground the first draft. Do not stop at the script output alone; still inspect the selected high-value modules directly.

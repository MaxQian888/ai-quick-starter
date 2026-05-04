# Debug Hypothesis Team — paste-in spawn brief

Use when a bug has 2-3 plausible root causes and you want them investigated in parallel rather than serially. Each teammate champions one hypothesis and tries to falsify the others.

## Prerequisites

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Subagent definitions: debugger
- A reproducible failure (deterministic repro is precondition — don't skip this)

## Paste-in prompt

```
Spawn a 3-teammate debug team to root-cause this failure:

Symptom: <pasted error / failing test name>
Repro: <exact command that reproduces it deterministically>
Surface area: <file paths most likely involved>
Already ruled out: <list — keeps teammates from re-treading>

Each teammate uses subagent type `debugger` but owns one hypothesis and is explicitly
adversarial to the others. Format: "I will prove H_X by finding evidence Y, and I will
try to falsify H_A and H_B by checking Z."

Hypotheses (fill these in):
- H_A: <e.g. "race condition in the streaming response handler">
- H_B: <e.g. "stale RSC cache holding a deleted record">
- H_C: <e.g. "type narrowing failure that bypasses the runtime check">

Teammates:
1. team-A — owns H_A. Must produce: minimal repro confirming OR refuting H_A.
   Writes findings to debug/<bug>-A.md.
2. team-B — owns H_B. Same contract for H_B. Writes to debug/<bug>-B.md.
3. team-C — owns H_C. Same contract for H_C. Writes to debug/<bug>-C.md.

Hard rules:
- No teammate may modify source files yet. This is investigation only.
- Each teammate must end its report with: "Confirmed | Refuted | Inconclusive" + evidence.
- Each teammate must list one falsification attempt against each rival hypothesis.
- If two teammates both Confirm, escalate to lead — they conflict by definition.

After all three: I (lead) read the three reports and decide which hypothesis to fix.
The fix happens in a separate session (not in this team) using the systematic-debugging skill.

Begin spawning all 3 in parallel.
```

## Notes

- Adversarial framing prevents the common failure mode where every teammate "confirms" their own hypothesis. Make the falsification step mandatory.
- Three hypotheses is the sweet spot. Two = no real diversity. Four+ = thrashing.
- Don't let teammates fix the bug. Investigation and fix are different skills; mixing them in a team produces overconfident patches.
- After fix, run the full test suite — agent team didn't write the fix, so verification is non-trivial.

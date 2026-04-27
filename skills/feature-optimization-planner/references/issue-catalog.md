# Issue Catalog

Use this checklist during the audit. Treat it as a scoring aid, not as permission to report every item mechanically.

## Priority Heuristics

### HIGH priority

- Security vulnerabilities or unsafe data handling
- Data corruption or correctness risks
- Blocking runtime bugs
- Clear critical performance bottlenecks on hot paths
- Missing validation on dangerous inputs or privileged flows

### MEDIUM priority

- Significant duplication or tangled ownership
- Missing or weak error handling
- Type-safety holes with realistic bug potential
- Missing tests on critical or failure-prone flows
- Performance waste that is noticeable but not catastrophic

### LOW priority

- Naming cleanup
- Documentation or comment gaps
- Minor style inconsistencies
- Small refactors with low user-facing impact

## 1. Structure And Organization

Check for:

- duplicated logic across files or branches,
- functions that are hard to scan because they are unusually long,
- files that mix unrelated responsibilities,
- deeply nested control flow,
- circular dependencies or cross-layer imports,
- module boundaries that force too many unrelated reasons to change together.

Evidence cues:

- repeated blocks with only small variable changes,
- files over roughly 300 lines without clear internal structure,
- nesting that exceeds three decision levels,
- import graphs that bounce between peer layers,
- helpers referenced from many unrelated domains.

## 2. Naming And Readability

Check for:

- inconsistent naming style inside the same folder,
- ambiguous names such as `data`, `temp`, `handler`, or `util`,
- magic numbers or string literals that should become named constants,
- complex logic with no explanation where explanation would save future readers time,
- stale comments that no longer match behavior.

Evidence cues:

- same concept named differently across files,
- boolean flags with unclear polarity,
- unexplained timeouts, sizes, retry counts, or status strings,
- comments that describe old behavior or contradict the code.

## 3. Error Handling

Check for:

- empty catch blocks,
- swallowed errors with no return-path signal,
- missing error boundaries or fallback handling,
- unhandled promise or async failure paths,
- missing input validation on public entrypoints.

Evidence cues:

- `catch {}` or `catch (e) {}` with no action,
- `await` chains that can fail without a visible caller guard,
- parse, decode, or network calls without validation or fallback,
- public functions that trust caller input blindly.

## 4. Performance

Check for:

- obviously inefficient loops or repeated scans,
- redundant computation in render or request paths,
- missing caching or memoization where expensive work repeats,
- large imports pulled into hot paths,
- lifecycle or subscription leaks,
- unnecessary rerenders in UI code.

Evidence cues:

- nested loops over the same collection,
- repeated filtering or mapping inside render bodies,
- event listeners or intervals without cleanup,
- whole-library imports where a narrower import exists,
- derived values recomputed on every call without need.

## 5. Type Safety

Check for:

- `any` or equivalent escape hatches,
- unsafe type assertions,
- missing annotations where inference is too weak,
- incomplete generics or unconstrained data shapes,
- unchecked deserialization or schema boundaries.

Evidence cues:

- `: any`, `as any`, broad `unknown` casts with no refinement,
- generic utilities that return vague shapes,
- runtime payloads used without schema validation,
- type guards missing around optional or union data.

## 6. Security

Check for:

- hardcoded secrets or credentials,
- unsafe shell, SQL, or HTML handling,
- missing auth or authorization checks around sensitive actions,
- unescaped rendering or unsafe content injection,
- insecure temporary-file or filesystem behavior.

Evidence cues:

- literal tokens, passwords, or API keys,
- string-built SQL or shell commands,
- `dangerouslySetInnerHTML`, `eval`, or equivalent dynamic execution,
- sensitive endpoints or commands with no visible access guard,
- user-controlled paths used directly.

## 7. Testing

Check for:

- missing test coverage on critical flows,
- weak assertions that prove little,
- missing edge cases or failure-path tests,
- flaky setup patterns,
- tests that mock too much and miss real behavior.

Evidence cues:

- feature files with no matching tests nearby or in the repo,
- assertions that only check truthiness or call count,
- no tests for empty, null, retry, timeout, auth, or permission paths,
- sleeps, timing hacks, or unstable ordering assumptions,
- tests that validate mocks more than product behavior.

## 8. Blind Spots To Report

Always note when the audit could not prove:

- runtime behavior,
- actual performance measurements,
- real authorization wiring,
- production-only configuration,
- hidden dependencies outside the target folder,
- coverage quality when tests were not executed.

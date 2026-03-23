# Teaching Patterns by Topic

Use these patterns when users ask for explanations on common programming topics.

## Table of Contents

1. Recursion
2. Time Complexity
3. Object-Oriented Design
4. Concurrency and Async
5. SQL Indexing
6. Memory and References
7. HTTP and API Design

## 1. Recursion

### Intuition Hook

- Frame recursion as "solve a smaller version of the same problem."
- Emphasize base case first, then recursive step.

### Mechanism Checklist

- Define input and output clearly.
- State base case and why it terminates.
- Show recursive case and how input size shrinks.
- Mention call stack behavior.

### Minimal Example Shape

- Factorial, tree traversal, or DFS with short code.
- Add one trace for a tiny input (`n=3` or one small tree).

### Common Traps

- Missing or incorrect base case.
- Recursive call that does not reduce problem size.
- Ignoring stack depth limits.

### Bridge Questions

- "What changes in each recursive call?"
- "Where does computation happen: before or after the recursive call?"

## 2. Time Complexity

### Intuition Hook

- Explain complexity as growth rate when input size increases.
- Separate asymptotic trend from constant-factor speed.

### Mechanism Checklist

- Identify the input variable (`n`, `m`, or both).
- Count dominant operations.
- Ignore constants and lower-order terms.
- Differentiate average vs worst case when relevant.

### Minimal Example Shape

- One loop (`O(n)`), nested loops (`O(n^2)`), binary search (`O(log n)`).
- Add a brief comparison table with practical thresholds.

### Common Traps

- Confusing runtime from one benchmark with complexity class.
- Mixing time and space complexity.
- Declaring `O(1)` for hash map operations without caveats.

### Bridge Questions

- "If input doubles, what should runtime roughly do?"
- "What operation dominates as `n` grows?"

## 3. Object-Oriented Design

### Intuition Hook

- Treat classes as contracts around behavior plus state.
- Distinguish interface from implementation.

### Mechanism Checklist

- Explain encapsulation, abstraction, composition, inheritance only as needed.
- Show responsibility boundaries for each class.
- Demonstrate dependency direction and coupling impact.

### Minimal Example Shape

- Payment strategy, notification channels, or repository pattern.
- Prefer composition-first example over inheritance-heavy example.

### Common Traps

- God objects that own too many responsibilities.
- Inheritance used for code reuse instead of type relationship.
- Leaky abstractions exposing internal details.

### Bridge Questions

- "Which object should own this behavior?"
- "Can this dependency be replaced without changing callers?"

## 4. Concurrency and Async

### Intuition Hook

- Define concurrency as coordination and parallelism as simultaneous execution.
- Explain async as non-blocking wait around I/O.

### Mechanism Checklist

- Identify whether workload is CPU-bound or I/O-bound.
- Explain event loop or scheduler role.
- Clarify ordering, cancellation, and error propagation.
- Mention shared-state safety when threads are involved.

### Minimal Example Shape

- Async HTTP calls with `await`.
- Producer-consumer queue.
- Lock-protected counter for race-condition demonstration.

### Common Traps

- Blocking call inside async workflow.
- Assuming task creation implies parallel execution.
- Ignoring cancellation and timeout paths.

### Bridge Questions

- "What is waiting, and what can run while waiting?"
- "What shared state can race?"

## 5. SQL Indexing

### Intuition Hook

- Compare index to an ordered lookup structure that avoids full table scans.
- Tie index value to read pattern, not to every column.

### Mechanism Checklist

- Start from query shape: `WHERE`, `JOIN`, `ORDER BY`.
- Discuss selectivity and cardinality.
- Explain composite index ordering.
- Mention read/write tradeoff and storage cost.

### Minimal Example Shape

- Query before and after index creation with conceptual plan difference.
- One composite index example showing left-prefix behavior.

### Common Traps

- Over-indexing every column.
- Wrong column order in composite index.
- Ignoring index maintenance overhead on heavy writes.

### Bridge Questions

- "Which query is slow and what predicate is used most?"
- "Does index order match your filter and sort path?"

## 6. Memory and References

### Intuition Hook

- Distinguish value copy from reference aliasing.
- Show mutation visibility across variables.

### Mechanism Checklist

- Explain stack/heap model as simplified mental model.
- Clarify object lifetime and garbage collection basics.
- Separate shallow copy and deep copy behavior.

### Minimal Example Shape

- Assign object to two variables, mutate one, observe both.
- Clone data safely with language-appropriate method.

### Common Traps

- Unexpected mutation through shared references.
- Assuming assignment always copies data.
- Confusing `const` with deep immutability.

### Bridge Questions

- "Are these two names pointing to the same object?"
- "What exactly is copied here?"

## 7. HTTP and API Design

### Intuition Hook

- Present API as a contract between client intent and server behavior.
- Emphasize resource modeling and predictable semantics.

### Mechanism Checklist

- Choose method semantics (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).
- Define request/response schema and error model.
- Explain idempotency and retries for write endpoints.
- Cover pagination, filtering, and versioning basics.

### Minimal Example Shape

- CRUD endpoints for one resource with status code rationale.
- Idempotency key example for create operations.

### Common Traps

- Treating all failures as `500`.
- Non-idempotent retry behavior.
- Inconsistent error format across endpoints.

### Bridge Questions

- "If client retries, what should happen?"
- "What contract must remain stable for existing clients?"

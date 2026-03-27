# Review Checklist

Run this checklist before returning the final command sequence.

- Is the shell explicit?
- Is the risk level explicit?
- Are the paths quoted correctly for the chosen shell?
- Does the answer avoid unconstrained wildcards or recursion where they are unsafe?
- Does the answer include `Pre-check` for every state-changing task?
- Does the answer include `Preview` for every high-risk task?
- Does the answer include `Verify` after every mutation?
- Does the answer explain elevation or privilege requirements when relevant?
- Does the answer avoid leading with the destructive command for high-risk work?
- For blocked work, does the answer avoid providing an execution command?

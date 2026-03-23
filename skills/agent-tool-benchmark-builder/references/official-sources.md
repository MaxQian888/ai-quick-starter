# Official Sources

Use these sources to anchor benchmark design decisions instead of relying on vague eval folklore.

## BFCL

Primary links:
- BFCL leaderboard: https://gorilla.cs.berkeley.edu/leaderboard
- BFCL overview: https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html
- BFCL live dataset: https://gorilla.cs.berkeley.edu/blogs/12_bfcl_v2_live.html
- BFCL multi-turn and multi-step: https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html
- BFCL format sensitivity: https://gorilla.cs.berkeley.edu/blogs/17_bfcl_v4_prompt_variation.html

Reusable takeaways:
- Split evaluation by scenario shape, not just a single aggregate score.
- Include "wrong to call any tool" cases, not only "pick the right tool" cases.
- Track both structured-match accuracy and executable outcome checks when possible.
- Expect real usage to skew heavily toward choosing between tools, not just parallel calls.
- Test prompt and output-format sensitivity if the benchmark must compare different runtimes.

## TRAJECT-Bench

Primary link:
- https://arxiv.org/abs/2510.04550

Reusable takeaways:
- Final-answer accuracy is not enough for tool agents.
- Report trajectory diagnostics separately:
  - tool selection
  - argument correctness
  - dependency or ordering satisfaction
- Design tasks with varying breadth and depth so model failure is attributable to the trajectory shape.

## ToolACE

Primary link:
- https://arxiv.org/abs/2409.00920

Reusable takeaways:
- Diverse APIs and diverse parameter shapes matter more than cosmetic prompt variation.
- Data quality control should combine rule-based verification with model-based review.
- Synthetic generation is useful only if the resulting calls are checked for coverage and correctness.

## How to Use These Sources

- Use BFCL patterns when defining benchmark taxonomy, abstention cases, and format sensitivity.
- Use TRAJECT-Bench patterns when the user asks for multi-step or order-sensitive trajectories.
- Use ToolACE patterns when you need to generate many tasks and want a quality-control pass instead of one-pass synthesis.

Do not blindly copy any single benchmark. Blend only the pieces that fit the user's target agent surface.

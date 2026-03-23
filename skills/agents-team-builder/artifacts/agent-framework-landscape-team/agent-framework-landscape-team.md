# agent-framework-landscape-team Agents Team Plan

## Request

Create a small Codex agent team that researches 12 to 15 current agent frameworks, prioritizes open-source options, includes a small number of representative official or commercial platforms, and delivers:

- a normalized comparison matrix
- a ranked selection conclusion with recommended tiers
- a phased implementation roadmap for proof-of-concept and adoption

## Assumptions

- Used `agent-framework-landscape-brief.md` as the primary request source.
- The generated first pass was refined manually because keyword heuristics collapsed the intended research workflow into generic implementation tasks.
- `.toml` files remain reviewable drafts and are not installed automatically.
- Open-source frameworks remain the priority, while official or commercial platforms serve only as representative context.

## Task Decomposition

- `freeze-scope-and-rubric`: Freeze Scope And Rubric (`lead`, `discovery`)
  Lock the sample pool, rubric, evidence standard, and merge rules before parallel research begins.
- `research-open-source-frameworks`: Research Open-Source Frameworks (`explorer`, `discovery`)
  Build evidence-backed framework cards for the primary open-source landscape.
- `research-representative-platforms`: Research Representative Official Or Commercial Platforms (`explorer`, `discovery`)
  Build comparable cards for a small number of representative official or commercial platforms.
- `normalize-comparison-matrix`: Normalize Comparison Matrix (`analyst`, `synthesis`)
  Merge both research tracks into a single comparable matrix and flag evidence gaps.
- `recommendation-and-roadmap`: Recommendation And Roadmap (`strategist`, `synthesis`)
  Convert the matrix into ranked recommendations, scenario-based picks, and a phased adoption roadmap.
- `final-package-review`: Final Package Review (`lead`, `verification`)
  Check traceability, cross-document consistency, and scope completeness before delivery.

## Parallelization Plan

- `discovery-research-batch`: tasks `research-open-source-frameworks`, `research-representative-platforms`
  Merge point: Lead confirms both evidence bundles are complete enough for analyst normalization before synthesis begins.

## Agent Team

- `lead` (`lead`): Own scope freeze, rubric integrity, merge points, and final delivery review. Owns `freeze-scope-and-rubric`, `final-package-review`.
- `explorer-open-source` (`explorer`): Research the open-source framework landscape with evidence-backed framework cards. Owns `research-open-source-frameworks`.
- `explorer-commercial` (`explorer`): Research representative official or commercial agent platforms for context and contrast. Owns `research-representative-platforms`.
- `analyst` (`analyst`): Normalize both research tracks into one comparison matrix with aligned scoring and explicit evidence gaps. Owns `normalize-comparison-matrix`.
- `strategist` (`strategist`): Convert the matrix into ranked recommendations, scenario-specific picks, and a phased implementation roadmap. Owns `recommendation-and-roadmap`.

## Prompt Templates

- `lead`: Use the lead agent to freeze the sample pool, evaluation rubric, merge rules, and final review boundary for the agent-framework research package.
- `explorer-open-source`: Use the explorer-open-source agent to research the open-source agent frameworks with official-source evidence and write framework cards against the frozen rubric.
- `explorer-commercial`: Use the explorer-commercial agent to research a small number of representative official or commercial platforms and write comparable evidence cards without expanding scope unnecessarily.
- `analyst`: Use the analyst agent to merge both research tracks into one normalized comparison matrix, align terminology, and flag evidence gaps.
- `strategist`: Use the strategist agent to turn the normalized matrix into ranked recommendations, scenario-specific picks, and a phased implementation roadmap.

## TOML Drafts

### lead.toml

```toml
name = "lead"
description = "Own scope freeze, rubric integrity, merge points, and final delivery review."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Atlas", "Beacon", "Helm"]
developer_instructions = """
Keep the team aligned on the frozen rubric, reject unsupported conclusions, and ensure every final recommendation is traceable back to the matrix.
"""
```

### explorer-open-source.toml

```toml
name = "explorer-open-source"
description = "Research the open-source framework landscape with evidence-backed framework cards."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
sandbox_mode = "read-only"
nickname_candidates = ["Scout", "Trace", "Lens"]
developer_instructions = """
Stay read-only, prioritize official docs and repositories, and report comparable evidence for each framework against the frozen rubric.
"""
```

### explorer-commercial.toml

```toml
name = "explorer-commercial"
description = "Research representative official or commercial agent platforms for context and contrast."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
sandbox_mode = "read-only"
nickname_candidates = ["Signal", "Pilot", "Scope"]
developer_instructions = """
Stay read-only, keep coverage intentionally selective, and focus on representative platforms that sharpen the final comparison rather than expanding the sample count without bound.
"""
```

### analyst.toml

```toml
name = "analyst"
description = "Normalize both research tracks into one comparison matrix with aligned scoring and explicit evidence gaps."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Matrix", "Grid", "Ledger"]
developer_instructions = """
Do not reopen research scope. Normalize terminology, flag missing evidence, and keep the matrix comparable across all frameworks and platforms.
"""
```

### strategist.toml

```toml
name = "strategist"
description = "Convert the matrix into ranked recommendations, scenario-specific picks, and a phased implementation roadmap."
model = "gpt-5.4"
model_reasoning_effort = "high"
tool_output_token_limit = 40000
model_reasoning_summary = "detailed"
model_verbosity = "high"
model_supports_reasoning_summaries = true
service_tier = "fast"
nickname_candidates = ["Northstar", "Route", "Frame"]
developer_instructions = """
Base every recommendation on matrix evidence, separate general-purpose picks from scenario-specific picks, and keep the roadmap constrained to realistic proof-of-concept and adoption phases.
"""
```

## Install Management

- Action: `install`
- Manifest: `C:\Users\qwdma\.codex\agents\.agents-team-builder\manifests\agent-framework-landscape-team.json`
- Installed files:
  `C:\Users\qwdma\.codex\agents\analyst.toml`
  `C:\Users\qwdma\.codex\agents\explorer-commercial.toml`
  `C:\Users\qwdma\.codex\agents\explorer-open-source.toml`
  `C:\Users\qwdma\.codex\agents\lead.toml`
  `C:\Users\qwdma\.codex\agents\strategist.toml`
- Install actions: `created` for all five files

## Execution Order

- Step 1: `freeze-scope-and-rubric`
  Lead publishes the rubric, sample pool, and evidence standard before any parallel research starts.
- Step 2: `research-open-source-frameworks`
  Explorer-open-source produces evidence-backed framework cards after the rubric is frozen.
- Step 3: `research-representative-platforms`
  Explorer-commercial produces comparable platform cards after the rubric is frozen.
- Step 4: `normalize-comparison-matrix`
  Analyst merges both evidence bundles into a normalized comparison matrix and gap log.
- Step 5: `recommendation-and-roadmap`
  Strategist turns the matrix into ranked recommendations, scenario picks, and a phased roadmap.
- Step 6: `final-package-review`
  Lead checks traceability, consistency, and scope before delivery.

## Risks And Guardrails

- If the lead does not freeze the rubric up front, the two research tracks will drift and the matrix will become non-comparable.
- Allowing either explorer to expand the framework list opportunistically will break the requested 12 to 15 framework budget and slow synthesis.
- If the analyst normalizes missing evidence into ratings, the selection conclusion will look precise without being trustworthy.
- Recommendation and roadmap work must stay serial after matrix normalization; starting them early would create unsupported conclusions.

## Open Questions

- Which 2 to 4 official or commercial platforms should be treated as representative context during stage 1 scope freeze?
- Should the final package include weighted scoring, or should the matrix remain qualitative with scenario-based recommendations?
- Do you want these TOML drafts to stay local artifacts, or should they later be promoted into persistent Codex agent configs after the team proves useful?

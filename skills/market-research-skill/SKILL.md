---
name: market-research-skill
description: |
  Use whenever you need to conduct structured market research, market sizing, competitor analysis, demand validation, pricing research, go-to-market planning, industry trend tracking, or decision memos that need evidence-based briefs with traceable sources. Make sure to use this skill whenever the user asks about "market", "competitors", "pricing", "demand", "opportunity", "landscape", "trends", "GTM", "go-to-market", "validation", "research brief", or "industry analysis" — even for niche or early-stage ideas with sparse data. Also trigger for investment memos, product strategy documents, or any request requiring external evidence and source links. Covers B2B and B2C contexts across software, hardware, and services.
---

# Market Research Skill

Run a repeatable market-research workflow and produce concise, evidence-first briefs.

## Adaptive Detection

Before starting research, detect the user's context:

1. **Industry signals**: Note the product domain (SaaS, AI, fintech, healthtech, consumer apps, etc.).
2. **Geography and ICP**: Identify target geography, customer segment, and company size.
3. **Time constraints**: Check if the user needs a quick scan (hours) or deep dive (days).
4. **Existing data**: Ask if the user has prior research, internal data, or known competitors.
5. **Decision type**: Determine if the output is for investment, product prioritization, pricing, or GTM planning.

Use these signals to tune query design, source selection, and output depth.

## Workflow

1. Define objective in one sentence and list constraints (time, budget, geography, ICP).
2. Build 2-6 focused queries using `references/query-patterns.md`.
3. Run `scripts/fetch_market_signals.py` to collect timestamped evidence with source links.
4. Cluster findings by signal type, competitor, and customer segment.
5. Score opportunities with the rubric in `references/research-playbook.md`.
6. Produce final brief with recommendation, confidence, evidence, risk, and next validation steps.

## Output Contract

Ensure every final market-research brief contains:

1. Scope: objective, segment, and timeframe.
2. Evidence table: headline, source link, publish time, and why it matters.
3. Competitor map: target customer, pricing posture, differentiation claim.
4. Opportunity scorecard: attractiveness, urgency, feasibility, defensibility.
5. Decision: pursue, monitor, or reject with explicit reasoning.

## Command Guide

Use query mode for trend and demand scans.

```bash
uv run --python 3.11 scripts/fetch_market_signals.py \
  --query "B2B onboarding automation" \
  --query "customer onboarding SaaS pricing"
```

Use mixed mode when users provide known feed URLs.

```bash
uv run --python 3.11 scripts/fetch_market_signals.py \
  --query "warehouse robotics startup funding" \
  --feed "https://techcrunch.com/category/startups/feed/" \
  --feed "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best" \
  --format markdown
```

Tune recall and precision:

- Increase `--lookback-days` for long-cycle markets.
- Increase `--max-per-query` for sparse niches.
- Use `--hl` and `--gl` to localize coverage.
- Use `--format json` for downstream automated scoring.

## Examples

### Example 1: Trend scan for a new product idea

```bash
uv run --python 3.11 scripts/fetch_market_signals.py \
  --query "AI coding assistant for enterprises" \
  --query "secure on-prem code generation" \
  --lookback-days 30 \
  --max-per-query 25 \
  --format markdown
```

### Example 2: Structured export for scoring

```bash
uv run --python 3.11 scripts/fetch_market_signals.py \
  --query "AI coding assistant for enterprises" \
  --lookback-days 30 \
  --max-per-query 25 \
  --format json \
  --output outputs/market_signals.json
```

## References

- Research framework and scoring rubric: `references/research-playbook.md`
- Query design templates: `references/query-patterns.md`
- Signal collection script: `scripts/fetch_market_signals.py`

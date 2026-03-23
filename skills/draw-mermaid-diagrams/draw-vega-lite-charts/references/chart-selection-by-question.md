# Chart Selection by Question

## Intent -> Chart Family

- Compare categories (single metric): `bar`
- Compare categories over time: `line` with `color` by category, or `facet` small multiples
- Trend over time: `line` or `area`
- Distribution of one metric: `bar` + binned `x`
- Relationship of two metrics: `point`
- Part-to-whole (few categories): `arc` or sorted `bar`
- Ranking / top N: sorted `bar` + optional `window` rank
- Before/after change: `bar` or `line` + `rule` baseline
- Composition over time: stacked `area` or stacked `bar`

## Channel Mapping Defaults

- Temporal progression:
  - `x`: temporal field (`type: temporal`, optional `timeUnit`)
  - `y`: quantitative metric
- Category comparison:
  - `x`: nominal category
  - `y`: quantitative aggregate
- Scatter:
  - `x`: quantitative metric A
  - `y`: quantitative metric B
  - `color`: nominal segment (optional)
  - `size`: quantitative weight (optional)

## Aggregation Rules

- If the metric is transactional (for example `amount`, `sales`), default to `aggregate: "sum"` unless user asks otherwise.
- If the metric is observational (for example `temperature`, `rating`), default to `aggregate: "mean"` for grouped views.
- If user asks for count and no metric column is provided, use `aggregate: "count"` without `field`.

## Time Rules

- Monthly trend: `timeUnit: "yearmonth"`
- Daily trend within one month: `timeUnit: "yearmonthdate"`
- Weekly trend: precompute week field or use date transform before plotting
- Keep time on `x` and metric on `y` unless user asks for horizontal orientation

## Sort Rules

- Category bars: default `sort: "-y"` when ranking matters.
- Time axes: keep natural temporal order.
- Stacked chart legend: sort by total value only if it improves readability.

## Escalation to Composition

Use composition only when necessary:

- Use `layer` for target lines, benchmarks, or annotations.
- Use `facet` when category count is manageable and per-panel comparison is needed.
- Use `concat` when two different but related views must be shown together.

## Quick Prompts -> Expected Specs

- "Show monthly revenue trend by region"
  - `mark`: line
  - `x`: month (temporal)
  - `y`: sum(revenue)
  - `color`: region

- "Which products are top 10 by sales?"
  - transform with `window` rank + `filter` rank <= 10
  - sorted bar chart

- "Is ad spend correlated with conversion rate?"
  - scatter chart with optional color by channel

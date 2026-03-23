# Vega-Lite Patterns

## Quick Selection Guide

- Use `bar` for category comparison.
- Use `line` for temporal trends.
- Use `point` for correlation and outliers.
- Use `area` for cumulative trends.
- Use `arc` for part-to-whole only when category count is small.

## Minimal Spec Skeleton

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": { "url": "data.csv" },
  "mark": "bar",
  "encoding": {
    "x": { "field": "category", "type": "nominal" },
    "y": { "field": "value", "type": "quantitative" }
  }
}
```

## Common Templates

### Aggregated Bar Chart

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": { "url": "data.csv" },
  "mark": "bar",
  "encoding": {
    "x": { "field": "department", "type": "nominal", "sort": "-y" },
    "y": { "aggregate": "sum", "field": "revenue", "type": "quantitative" },
    "tooltip": [
      { "field": "department", "type": "nominal" },
      { "aggregate": "sum", "field": "revenue", "type": "quantitative" }
    ]
  }
}
```

### Time Series Line Chart

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": { "url": "data.csv" },
  "mark": { "type": "line", "point": true },
  "encoding": {
    "x": { "field": "date", "type": "temporal", "timeUnit": "yearmonth" },
    "y": { "aggregate": "sum", "field": "sales", "type": "quantitative" },
    "color": { "field": "region", "type": "nominal" }
  }
}
```

### Scatter Plot

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": { "url": "data.csv" },
  "mark": "point",
  "encoding": {
    "x": { "field": "ad_spend", "type": "quantitative" },
    "y": { "field": "conversion_rate", "type": "quantitative" },
    "size": { "field": "sessions", "type": "quantitative" },
    "color": { "field": "channel", "type": "nominal" }
  }
}
```

## Transform Patterns

- Use `calculate` to derive fields from existing columns.
- Use `filter` to keep relevant subsets.
- Use `window` for rank and running totals.
- Use `joinaggregate` for percent-of-total style metrics.

Example:

```json
"transform": [
  { "filter": "datum.sales != null" },
  { "calculate": "datum.sales * 1.13", "as": "sales_with_tax" }
]
```

## Composition Patterns

- Use `layer` for overlays like line + points + threshold rule.
- Use `facet` for small multiples by category.
- Use `concat` for side-by-side comparisons with shared style.

## Frequent Pitfalls

- Do not mark date strings as `nominal` when trend over time is required.
- Do not combine aggregated and non-aggregated channels unless grouping is explicit.
- Do not overuse color for high-cardinality categories.
- Do not use pie charts for many slices; switch to sorted bars.

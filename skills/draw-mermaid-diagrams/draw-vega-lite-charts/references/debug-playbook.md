# Vega-Lite Debug Playbook

## Triage Order

1. Validate JSON syntax (commas, braces, quotes).
2. Validate required top-level keys (`$schema`, `data`, `mark`, `encoding`).
3. Validate field names against actual dataset columns.
4. Validate channel types and aggregate/grouping coherence.
5. Isolate transforms and composition blocks.

## Symptom -> Fix

### Parser Error / Invalid JSON

- Symptom: spec cannot parse at all.
- Check:
  - Trailing commas
  - Single quotes instead of double quotes
  - Non-JSON comments
- Fix:
  - Convert to strict JSON and retry.

### Blank Chart

- Symptom: chart renders axes but no marks, or totally empty.
- Check:
  - `data.url` path is reachable
  - filter removes all rows
  - field names are misspelled
  - temporal values are parseable dates
- Fix:
  - Temporarily remove `transform` and test with raw rows.
  - Replace `data.url` with a known sample to isolate data source issues.

### Wrong Aggregated Values

- Symptom: totals or averages look incorrect.
- Check:
  - accidental double aggregation
  - mixed aggregated and non-aggregated encodings
  - missing grouping dimension
- Fix:
  - Make all measure channels consistently aggregated, or none.
  - Add explicit grouping dimension in `x`, `color`, or `detail`.

### "Temporal" Not Behaving as Time

- Symptom: points appear unordered or treated like categories.
- Check:
  - string format is not recognized as date
  - incorrect `type` set to `nominal`
  - wrong `timeUnit`
- Fix:
  - Set channel `type: "temporal"`.
  - Use `calculate` to normalize date strings if needed.

### Overloaded Colors / Illegible Legend

- Symptom: too many colors and unreadable chart.
- Check:
  - high-cardinality field mapped to `color`
- Fix:
  - move high-cardinality dimension to `facet` or tooltip.
  - keep `color` for low-cardinality segments.

### Layer / Facet / Concat Breaks Output

- Symptom: composition added and chart fails or becomes misleading.
- Check:
  - mismatched shared encodings
  - incompatible scales or projections
- Fix:
  - Start from one view and add composition pieces one at a time.
  - Keep each child spec independently valid before combining.

## Safe Rollback Strategy

When complex specs fail:

1. Keep data source unchanged.
2. Remove transforms.
3. Remove composition (`layer`/`facet`/`concat`).
4. Keep one mark + one x + one y.
5. Reintroduce features in this order:
   - aggregate
   - filter/calculate
   - tooltip/sort
   - color/size/detail
   - composition

## Minimal Known-Good Baseline

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

# Benchmark Report: shadcn-component-migrator

## Iteration 1

### Pass Rates

| Eval | with_skill | without_skill | Delta |
|------|-----------|---------------|-------|
| simple-components-migration | 100% (5/5) | 40% (2/5) | +60% |
| complex-components-skipped | 100% (3/3) | 100% (3/3) | 0% |
| responsive-classes-preserved | 100% (7/7) | 100% (7/7) | 0% |
| **Overall** | **100% (15/15)** | **80% (12/15)** | **+20%** |

### Timing

| Config | Mean Duration | StdDev |
|--------|--------------|--------|
| with_skill | 256.3s | 147.3s |
| without_skill | 132.8s | 30.0s |

### Tokens

| Config | Mean Tokens | StdDev |
|--------|------------|--------|
| with_skill | 37,986 | 1,304 |
| without_skill | 39,313 | 1,432 |

### Analyst Observations

1. **Simple component migration is where the skill shines**: The baseline completely failed to use actual shadcn/ui components, instead recreating them inline with cva. The skill correctly imported and used `Button`, `Badge`, and `Separator` from `@/components/ui/*`.

2. **Complex component filtering is equivalent**: Both skill and baseline correctly skipped composite components and hook-heavy components. This is a non-discriminating assertion — it passes regardless of skill.

3. **Responsive preservation is equivalent on key classes**: Both skill and baseline preserved the responsive Tailwind classes. However, the baseline lost some non-responsive base classes (`gap-2`, `rounded-lg`, `p-3`) which could affect visual appearance even though they weren't explicitly asserted.

4. **Time cost**: The skill runs take roughly 2x longer. This is likely due to the larger context window from loading the skill instructions. The tradeoff is justified given the correctness improvement on simple migrations.

5. **Token usage**: Surprisingly, the skill uses slightly fewer tokens on average despite the longer runtime. This suggests the skill helps the model be more focused in its output.

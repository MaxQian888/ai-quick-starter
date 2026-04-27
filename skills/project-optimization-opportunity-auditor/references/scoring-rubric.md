# Scoring Rubric

## Dimensions

- **Impact**: expected value if solved.
- **Urgency**: how soon it should be addressed.
- **Confidence**: how strong the observed evidence is.
- **Effort**: estimated implementation cost (higher = more expensive).

## Score Formula

`score = impact*3 + urgency*2 + confidence*2 - effort`

## Priority Bands

- `high`: score >= 20
- `medium`: 13 <= score < 20
- `low`: score < 13

## Tie-Break Rules

When scores are tied:

1. Higher confidence first.
2. Lower effort first.
3. Broader cross-file evidence first.

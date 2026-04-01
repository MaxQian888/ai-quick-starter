# Style Sampling

Read this file before deciding how much comment cleanup to do.

## Sampling Order

1. Same file, if it already contains a few strong comments.
2. Same directory, same language.
3. Nearest sibling directory in the same layer, same language.
4. Shared helpers in the same language only when the target area is nearly comment-free.

Do not sample from generated files, tests, or example fixtures unless the user explicitly asked to edit those surfaces too.

## What To Compare

- Comment density: sparse, moderate, or dense.
- Comment placement: header comments, docstrings, inline comments, or mixed.
- Sentence shape: short fragments, full sentences, or terse bullet-like phrasing.
- Vocabulary: domain terms, abbreviations, and naming already used nearby.
- Language choice: Chinese, English, or mixed.

## Decision Rules

- If the local area is sparse, add only the missing comments that explain intent, hazards, or edge cases.
- If the local area already has solid comments, match their tone before touching weaker ones.
- If two styles conflict, prefer the style used most often in the same language and same layer.
- If the evidence is weak, stay conservative and explain the uncertainty in the final report.

## Stop Signs

- The only nearby comments live in generated or vendor files.
- The target file belongs to a totally different language style than the rest of the directory.
- The target already has a strong comment pattern and the requested rewrite would overwrite it with generic prose.

When any stop sign appears, narrow the edit scope and sample more carefully before rewriting comments.

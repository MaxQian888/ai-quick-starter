# Project Scan Guide

## Read Order

1. Root guidance files (`AGENTS.md`, `CLAUDE.md`, `README*`).
2. Build and package manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`).
3. Target module docs and tests.

## Stop Conditions

Stop scanning once you can answer:

- scope boundaries,
- editable paths,
- validation commands,
- expected output shape.

If one of these remains unknown, do one narrow follow-up read.

# Changelog

All notable changes to this repository will be documented in this file.

This project follows a simple Keep a Changelog style and semantic versioning for Claude plugin metadata.

## [0.1.1] - 2026-03-23

### Added
- Marketplace plugin generator at `scripts/build_marketplace_plugins.py`
- Regression test coverage for per-skill plugin generation at `tests/test_build_marketplace_plugins.py`
- Generated standalone marketplace plugin directories under `plugins/`

### Changed
- Marketplace catalog now lists the bundle plugin plus each top-level skill as an individually installable plugin
- Marketplace plugin generation now uses link/junction wrappers by default so `skills/` stays the single source of truth for standard skills CLI installs
- README installation docs now explain both single-skill installs and bundle installs
- Claude plugin manifest version bumped to `0.1.1`

## [0.1.0] - 2026-03-23

### Added
- Bilingual public repository README for GitHub and Claude Code users
- MIT license and GitHub community-health files
- Claude Code plugin manifest at `.claude-plugin/plugin.json`
- Claude Code marketplace catalog at `.claude-plugin/marketplace.json`
- GitHub issue templates and pull request template
- In-repo `skills/stock-analyzer-skill` skill content
- In-repo `skills/code-simplifier` skill with refinement-scope detection, references, and tests

# CHANGELOG Format Reference

This reference covers common CHANGELOG formats and best practices.

## Keep a Changelog Format (Recommended)

The most widely adopted format. Structure:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New feature description

### Changed
- Change in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security-related changes

## [1.2.0] - 2024-01-15

### Added
- Feature X that does Y

### Fixed
- Bug where Z would cause crash (#123)
```

### Categories

| Category | When to Use |
|----------|-------------|
| **Added** | New features |
| **Changed** | Changes to existing functionality |
| **Deprecated** | Features marked for removal |
| **Removed** | Removed features |
| **Fixed** | Bug fixes |
| **Security** | Vulnerability fixes |

### Version Format

```
## [MAJOR.MINOR.PATCH] - YYYY-MM-DD
```

- Add release dates
- Link to version diffs at the bottom
- Group changes by category within each version

## Conventional Changelog (Commit-Based)

If the project uses conventional commits, the CHANGELOG may be
auto-generated. In this case:

- Follow the existing auto-generated format
- Ensure commit messages are descriptive
- Group by commit type: `feat`, `fix`, `docs`, `style`, `refactor`, etc.

Example:
```markdown
# [1.2.0](https://github.com/user/repo/compare/v1.1.0...v1.2.0) (2024-01-15)

### Features
* add support for JSON output ([abc1234](...))
* implement batch processing ([def5678](...))

### Bug Fixes
* correct handling of empty arrays ([ghi9012](...))
```

## Simple List Format

Some projects use a simpler format:

```markdown
# Changelog

## 1.2.0 (2024-01-15)
- Added: JSON output support
- Added: Batch processing mode
- Fixed: Empty array handling
- Changed: Improved error messages
```

## Writing Good Changelog Entries

### Do:
- Write for users, not developers
- Explain the impact: what changed and why it matters
- Reference issue/PR numbers when available
- Use present tense: "Add feature" not "Added feature"
- Be specific: "Add CSV export" not "Add new export format"

### Don't:
- Include internal refactoring with no user impact
- Write vague entries like "various fixes"
- Include every commit — group related changes
- Use commit messages verbatim unless they're already clear

### Examples

| Bad | Good |
|-----|------|
| Fixed bug | Fixed crash when parsing malformed YAML |
| Updated deps | Updated lodash to 4.17.21 to fix CVE-2021-23337 |
| New feature | Added `--format json` flag for machine-readable output |
| Refactor | *(omit if no user impact)* |

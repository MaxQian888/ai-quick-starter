# Verified Component Snapshot

This is a dated snapshot taken on `2026-04-09`. Re-run `scripts/discover_latest_actions.py` before editing workflows so the final change uses live data instead of this snapshot alone.

## Verified release snapshot

| Component | Latest verified tag on 2026-04-09 | Source |
| --- | --- | --- |
| `actions/checkout` | `v6.0.2` | `https://github.com/actions/checkout/releases/tag/v6.0.2` |
| `actions/cache` | `v5.0.4` | `https://github.com/actions/cache/releases/tag/v5.0.4` |
| `actions/setup-node` | `v6.3.0` | `https://github.com/actions/setup-node/releases/tag/v6.3.0` |
| `actions/setup-python` | `v6.2.0` | `https://github.com/actions/setup-python/releases/tag/v6.2.0` |
| `actions/setup-go` | `v6.4.0` | `https://github.com/actions/setup-go/releases/tag/v6.4.0` |
| `actions/setup-java` | `v5.2.0` | `https://github.com/actions/setup-java/releases/tag/v5.2.0` |
| `actions/setup-dotnet` | `v5.2.0` | `https://github.com/actions/setup-dotnet/releases/tag/v5.2.0` |
| `actions/upload-artifact` | `v7.0.0` | `https://github.com/actions/upload-artifact/releases/tag/v7.0.0` |
| `actions/download-artifact` | `v8.0.1` | `https://github.com/actions/download-artifact/releases/tag/v8.0.1` |
| `docker/setup-buildx-action` | `v4.0.0` | `https://github.com/docker/setup-buildx-action/releases/tag/v4.0.0` |
| `docker/login-action` | `v4.1.0` | `https://github.com/docker/login-action/releases/tag/v4.1.0` |
| `docker/build-push-action` | `v7.0.0` | `https://github.com/docker/build-push-action/releases/tag/v7.0.0` |
| `pnpm/action-setup` | `v5.0.0` | `https://github.com/pnpm/action-setup/releases/tag/v5.0.0` |
| `astral-sh/setup-uv` | `v8.0.0` | `https://github.com/astral-sh/setup-uv/releases/tag/v8.0.0` |
| `github/codeql-action` | `codeql-bundle-v2.25.1` | `https://github.com/github/codeql-action/releases/tag/codeql-bundle-v2.25.1` |

## Use this snapshot correctly

- Treat the table as a freshness anchor, not as the final source of truth.
- Prefer SHA-pinned `uses:` lines generated from the live resolver.
- Re-run verification after changing the stack or adding a new third-party action.
- For local and private actions, public release metadata is not enough; inspect their repos directly.

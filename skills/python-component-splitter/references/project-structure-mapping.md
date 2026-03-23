# Project Structure Mapping

Use this reference when mapping a large Python module into smaller files.

## Detect Existing Conventions First

Inspect nearby directories and reuse existing naming before introducing new folders.

- If the repository already has `src/`, keep new components under `src/`.
- If modules are grouped by domain (`orders/`, `billing/`), split inside that domain first.
- If layered names already exist (`services/`, `repositories/`, `schemas/`), keep using them.
- If ports/adapters naming exists (`domain/`, `application/`, `infrastructure/`), keep that structure.

## Style Selection Rules

Pick one style per refactor and stay consistent.

1. Choose `hexagonal` when `domain`, `application`, and `infrastructure` are already present.
2. Choose `layered` when the project already separates API/service/repository/model concerns.
3. Choose `package` when the project is simple and does not expose strong architecture markers.

## Symbol-to-File Mapping

Use this default mapping unless existing project conventions contradict it.

| Symbol Kind | Layered | Hexagonal | Package |
|---|---|---|---|
| Controller / Handler | `api.py` | `interfaces/api.py` | `api.py` |
| Service / Manager | `services.py` | `application/services.py` | `services.py` |
| Repository / DAO | `repositories.py` | `infrastructure/repositories.py` | `persistence.py` |
| Entity / Model | `models.py` | `domain/entities.py` | `models.py` |
| Schema / DTO | `schemas.py` | `interfaces/schemas.py` | `schemas.py` |
| Validation / Parsing | `validators.py` | `application/validators.py` | `validators.py` |
| Read queries | `queries.py` | `application/queries.py` | `queries.py` |
| Write operations | `commands.py` | `application/commands.py` | `operations.py` |
| Shared helpers | `utils.py` | `shared/utils.py` | `utils.py` |

## Migration Safety Rules

- Keep the original module as a compatibility shim until downstream imports are migrated.
- Move symbols in small batches and run tests between batches.
- Prefer copying then switching imports; avoid one-shot massive moves.
- Keep public API in `__init__.py` explicit (`__all__`) when package becomes external surface.
- Delete shim only after search confirms no remaining imports of the old module path.

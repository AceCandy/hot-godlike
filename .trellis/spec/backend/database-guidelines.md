# Database Guidelines

> Database patterns and conventions for this project.

---

## Overview

<!--
Document your project's database conventions here.

Questions to answer:
- What ORM/query library do you use?
- How are migrations managed?
- What are the naming conventions for tables/columns?
- How do you handle transactions?
-->

(To be filled by the team)

---

## Query Patterns

<!-- How should queries be written? Batch operations? -->

(To be filled by the team)

---

## Migrations

<!-- How to create and run migrations -->

(To be filled by the team)

---

## Naming Conventions

<!-- Table names, column names, index names -->

(To be filled by the team)

---

## Common Mistakes

<!-- Database-related mistakes your team has made -->

### Scenario: Explicit Local Collection Storage

#### 1. Scope / Trigger

- Trigger: backend storage wiring for M2 source registry and collection data.
- Applies when adding or modifying source, fetch run, raw item, or source health persistence.
- `STORAGE_MODE=local` is a durable local development mode, not a hidden fallback.

#### 2. Signatures

- `build_source_repository(storage_mode, local_sqlite_path, use_postgres, postgres_dsn)`
- `build_collection_store(storage_mode, local_sqlite_path, use_postgres, postgres_dsn)`
- `SqliteSourceRepository.from_path(path: str)`
- `SqliteCollectionStore.from_path(path: str)`
- SQLite tables: `sources`, `fetch_runs`, `raw_items`, `source_health`

#### 3. Contracts

- `STORAGE_MODE=memory`: use in-memory stores only; data may be lost on restart.
- `STORAGE_MODE=local`: persist source and collection data to SQLite.
- `STORAGE_MODE=postgres`: use PostgreSQL for source and collection stores.
- `LOCAL_STORAGE_PATH`: optional for local mode; default is `backend/data/hot_godlike.sqlite`.
- Local mode must persist the same contract-shaped fields returned by PostgreSQL stores.

#### 4. Validation & Error Matrix

- Unknown `STORAGE_MODE` -> `RuntimeError`.
- `STORAGE_MODE=local` without a local path -> `RuntimeError`.
- `STORAGE_MODE=postgres` without `DATABASE_URL` or `POSTGRES_DSN` -> `RuntimeError`.
- Missing source / fetch run / raw item must still map to the existing contract errors.

#### 5. Good/Base/Bad Cases

- Good: `STORAGE_MODE=local LOCAL_STORAGE_PATH=/tmp/hot.sqlite uvicorn app.main:app --reload`
- Base: no storage mode, no PostgreSQL flags -> in-memory dev/test stores.
- Bad: silently writing local files because PostgreSQL env vars are missing.

#### 6. Tests Required

- Store tests must prove source, fetch run, raw item, and source health survive reopening the SQLite store.
- Raw item tests must assert source-level dedupe still returns duplicate counts.
- API-level tests must prove `create_app` wires source and collection stores to the same SQLite file.
- Builder tests must prove explicit local mode selects SQLite and default mode remains in-memory.

#### 7. Wrong vs Correct

Wrong:

```python
# Hides a production misconfiguration and makes persistence ambiguous.
try:
    return PostgresCollectionStore.from_dsn(dsn)
except RuntimeError:
    return SqliteCollectionStore.from_path("backend/data/hot_godlike.sqlite")
```

Correct:

```python
if storage_mode == "local":
    return SqliteCollectionStore.from_path(local_sqlite_path)
if storage_mode == "postgres":
    return PostgresCollectionStore.from_dsn(postgres_dsn)
```

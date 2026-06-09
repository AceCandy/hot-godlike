from pathlib import Path


MIGRATION = Path(__file__).resolve().parents[1] / "migrations" / "001_m2_collection_schema.sql"


def test_m2_collection_migration_defines_required_tables() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    for table in ("sources", "fetch_runs", "raw_items", "source_health"):
        assert f"create table if not exists {table}" in sql


def test_m2_collection_migration_defines_constraints_and_indexes() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "references sources(id)" in sql
    assert "create unique index if not exists ux_fetch_runs_source_idempotency_key" in sql
    assert "on fetch_runs (source_id, idempotency_key)" in sql
    assert "where idempotency_key is not null" in sql
    assert "unique (source_id, dedupe_key)" in sql
    assert "create index if not exists idx_raw_items_source_fetched_at" in sql
    assert "create index if not exists idx_raw_items_status_fetched_at" in sql
    assert "create index if not exists idx_raw_items_normalized_url" in sql


def test_m2_collection_migration_keeps_etag_last_modified_columns() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "etag text null" in sql
    assert "last_modified text null" in sql
    assert "last_fetched_at timestamptz null" in sql

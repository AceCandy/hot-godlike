from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any


SqliteConnectionFactory = Callable[[], sqlite3.Connection]
STORAGE_MODES = {"memory", "local", "postgres"}


def sqlite_connection_factory(path: str) -> SqliteConnectionFactory:
    db_path = Path(path).expanduser()
    if str(db_path) != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect() -> sqlite3.Connection:
        connection = sqlite3.connect(str(db_path))
        connection.row_factory = sqlite3.Row
        connection.execute("pragma foreign_keys = on")
        return connection

    return connect


def normalize_storage_mode(storage_mode: str | None) -> str | None:
    if not storage_mode:
        return None
    value = storage_mode.strip().lower()
    if value not in STORAGE_MODES:
        raise RuntimeError("STORAGE_MODE 仅支持 memory、local 或 postgres。")
    return value


def ensure_collection_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(_SQLITE_COLLECTION_SCHEMA)
    connection.commit()


def sqlite_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: sqlite_value(value) for key, value in params.items()}


def sqlite_value(value: Any) -> Any:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, datetime):
        normalized = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return normalized.isoformat().replace("+00:00", "Z")
    return value


_SQLITE_COLLECTION_SCHEMA = """
create table if not exists sources (
    id text primary key,
    name text not null,
    type text not null,
    category text not null,
    url text null,
    route text null,
    enabled integer not null,
    status text not null,
    fetch_interval_minutes integer not null,
    timeout_seconds integer not null,
    retry_count integer not null,
    concurrency_limit integer not null,
    trust_level text not null,
    requires_cookie integer not null default 0,
    first_fetch_mode text not null default 'ingest_only',
    etag text null,
    last_modified text null,
    last_fetched_at text null,
    created_at text not null,
    updated_at text not null
);

create table if not exists fetch_runs (
    id text primary key,
    source_id text not null references sources(id),
    trigger text not null,
    status text not null,
    started_at text not null,
    finished_at text null,
    duration_ms integer null,
    fetched_count integer not null default 0,
    new_count integer not null default 0,
    duplicate_count integer not null default 0,
    ignored_count integer not null default 0,
    error_code text null,
    error_message text null,
    trace_id text not null,
    idempotency_key text null
);

create unique index if not exists ux_fetch_runs_source_idempotency_key
    on fetch_runs (source_id, idempotency_key)
    where idempotency_key is not null;

create table if not exists raw_items (
    id text primary key,
    source_id text not null references sources(id),
    source_name text not null,
    title text not null,
    url text not null,
    normalized_url text not null,
    published_at text null,
    fetched_at text not null,
    author text null,
    summary text null,
    content_snippet text null,
    hot_score text null,
    rank integer null,
    image text null,
    raw_payload_ref text null,
    status text not null,
    dedupe_key text not null,
    created_at text not null,
    unique (source_id, dedupe_key)
);

create index if not exists idx_raw_items_source_fetched_at
    on raw_items (source_id, fetched_at desc);

create index if not exists idx_raw_items_status_fetched_at
    on raw_items (status, fetched_at desc);

create index if not exists idx_raw_items_normalized_url
    on raw_items (normalized_url);

create table if not exists source_health (
    source_id text primary key references sources(id),
    status text not null,
    last_succeeded_at text null,
    last_failed_at text null,
    consecutive_failures integer not null default 0,
    next_fetch_at text null,
    circuit_opened_at text null,
    degraded_until text null,
    last_error_code text null,
    last_error_message text null,
    updated_at text not null
);
"""

-- M2 collection schema for source registry, fetch runs, raw items, and source health.

create table if not exists sources (
    id text primary key,
    name text not null,
    type text not null,
    category text not null,
    url text null,
    route text null,
    enabled boolean not null,
    status text not null,
    fetch_interval_minutes integer not null,
    timeout_seconds integer not null,
    retry_count integer not null,
    concurrency_limit integer not null,
    trust_level text not null,
    requires_cookie boolean not null default false,
    first_fetch_mode text not null default 'ingest_only',
    etag text null,
    last_modified text null,
    last_fetched_at timestamptz null,
    created_at timestamptz not null,
    updated_at timestamptz not null
);

create table if not exists fetch_runs (
    id text primary key,
    source_id text not null references sources(id),
    trigger text not null,
    status text not null,
    started_at timestamptz not null,
    finished_at timestamptz null,
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
    published_at timestamptz null,
    fetched_at timestamptz not null,
    author text null,
    summary text null,
    content_snippet text null,
    hot_score text null,
    rank integer null,
    image text null,
    raw_payload_ref text null,
    status text not null,
    dedupe_key text not null,
    created_at timestamptz not null,
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
    last_succeeded_at timestamptz null,
    last_failed_at timestamptz null,
    consecutive_failures integer not null default 0,
    next_fetch_at timestamptz null,
    circuit_opened_at timestamptz null,
    degraded_until timestamptz null,
    last_error_code text null,
    last_error_message text null,
    updated_at timestamptz not null
);

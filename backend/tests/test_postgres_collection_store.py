from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.core.errors import ErrorCode, QueryServiceError
from app.services.collection_store import PostgresCollectionStore


class FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def fetchone(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self._rows)


class FakePostgresState:
    def __init__(self) -> None:
        self.runs: dict[str, dict[str, Any]] = {}
        self.raw_items: dict[str, dict[str, Any]] = {}
        self.health: dict[str, dict[str, Any]] = {}
        self.dedupe_keys: set[tuple[str, str]] = set()
        self.executed: list[str] = []
        self.commits = 0


class FakePostgresConnection:
    def __init__(self, state: FakePostgresState) -> None:
        self._state = state

    def __enter__(self) -> "FakePostgresConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> FakeCursor:
        normalized_sql = " ".join(sql.lower().split())
        self._state.executed.append(normalized_sql)
        params = params or {}

        if "from fetch_runs" in normalized_sql and "idempotency_key" in normalized_sql:
            rows = [
                run
                for run in self._state.runs.values()
                if run["source_id"] == params["source_id"] and run.get("idempotency_key") == params["idempotency_key"]
            ]
            return FakeCursor(rows[:1])

        if normalized_sql.startswith("insert into fetch_runs"):
            self._state.runs[params["id"]] = _run_row(params)
            return FakeCursor([self._state.runs[params["id"]]])

        if normalized_sql.startswith("update fetch_runs"):
            row = self._state.runs.get(params["run_id"])
            if not row:
                return FakeCursor([])
            row.update(_run_finish_update(params))
            return FakeCursor([row])

        if "from fetch_runs where id" in normalized_sql:
            row = self._state.runs.get(params["run_id"])
            return FakeCursor([row] if row else [])

        if normalized_sql.startswith("select * from fetch_runs"):
            rows = list(self._state.runs.values())
            if params.get("source_id"):
                rows = [row for row in rows if row["source_id"] == params["source_id"]]
            if params.get("status"):
                rows = [row for row in rows if row["status"] == params["status"]]
            return FakeCursor(rows[: params["limit"]])

        if normalized_sql.startswith("insert into raw_items"):
            key = (params["source_id"], params["dedupe_key"])
            if key in self._state.dedupe_keys:
                return FakeCursor([])
            self._state.dedupe_keys.add(key)
            self._state.raw_items[params["id"]] = _raw_item_row(params)
            return FakeCursor([{"id": params["id"]}])

        if "from raw_items where id" in normalized_sql:
            row = self._state.raw_items.get(params["raw_item_id"])
            return FakeCursor([row] if row else [])

        if normalized_sql.startswith("select * from raw_items"):
            rows = list(self._state.raw_items.values())
            if params.get("source_id"):
                rows = [row for row in rows if row["source_id"] == params["source_id"]]
            if params.get("status"):
                rows = [row for row in rows if row["status"] == params["status"]]
            if params.get("q"):
                needle = params["q"].strip("%").lower()
                rows = [row for row in rows if needle in row["title"].lower()]
            return FakeCursor(rows[: params["limit"]])

        if "from source_health where source_id" in normalized_sql:
            row = self._state.health.get(params["source_id"])
            return FakeCursor([row] if row else [])

        if normalized_sql.startswith("insert into source_health"):
            self._state.health[params["source_id"]] = _health_row(params)
            return FakeCursor([self._state.health[params["source_id"]]])

        if normalized_sql.startswith("select * from source_health"):
            rows = list(self._state.health.values())
            if params.get("source_id"):
                rows = [row for row in rows if row["source_id"] == params["source_id"]]
            if params.get("status"):
                rows = [row for row in rows if row["status"] == params["status"]]
            return FakeCursor(rows[: params["limit"]])

        raise AssertionError(f"Unexpected SQL: {sql}")

    def commit(self) -> None:
        self._state.commits += 1


def make_store(state: FakePostgresState) -> PostgresCollectionStore:
    return PostgresCollectionStore(lambda: FakePostgresConnection(state))


def test_postgres_collection_store_round_trips_run_raw_items_and_health() -> None:
    state = FakePostgresState()
    store = make_store(state)
    source = source_payload()

    assert store.existing_idempotent_run(source["id"], "manual-1") is None
    run = store.start_run(source_id=source["id"], trigger="manual", idempotency_key="manual-1")
    existing = store.existing_idempotent_run(source["id"], "manual-1")
    finished = store.finish_run(
        run["id"],
        status="succeeded",
        fetched_count=2,
        new_count=1,
        duplicate_count=1,
        ignored_count=0,
    )
    new_count, duplicate_count = store.save_raw_items([raw_item_payload(source), raw_item_payload(source, item_id="raw_dup")])
    health = store.record_success(source)
    runs = store.list_runs(source_id=source["id"], status="succeeded", take=10)
    raw_items = store.list_raw_items(source_id=source["id"], status="new", q="first", take=10)
    health_items = store.list_health(source_id=source["id"], status="enabled", take=10)

    assert existing is not None
    assert existing["id"] == run["id"]
    assert finished["status"] == "succeeded"
    assert finished["newCount"] == 1
    assert new_count == 1
    assert duplicate_count == 1
    assert store.get_raw_item(raw_items["items"][0]["id"])["normalizedUrl"] == "https://example.com/item"
    assert store.get_run(run["id"])["traceId"].startswith("tr_")
    assert health["sourceId"] == source["id"]
    assert health["consecutiveFailures"] == 0
    assert runs["items"][0]["id"] == run["id"]
    assert raw_items["items"][0]["title"] == "First item"
    assert health_items["items"][0]["status"] == "enabled"
    assert state.commits >= 4
    assert any("insert into fetch_runs" in sql for sql in state.executed)
    assert any("insert into raw_items" in sql for sql in state.executed)
    assert any("insert into source_health" in sql for sql in state.executed)


def test_postgres_collection_store_records_failure_thresholds() -> None:
    store = make_store(FakePostgresState())
    source = source_payload()

    first = store.record_failure(source, error_code="SOURCE_TIMEOUT", error_message="timeout")
    second = store.record_failure(source, error_code="SOURCE_TIMEOUT", error_message="timeout")
    third = store.record_failure(source, error_code="SOURCE_TIMEOUT", error_message="timeout")
    store.record_failure(source, error_code="SOURCE_TIMEOUT", error_message="timeout")
    fifth = store.record_failure(source, error_code="SOURCE_TIMEOUT", error_message="timeout")

    assert first["status"] == "enabled"
    assert second["consecutiveFailures"] == 2
    assert third["status"] == "degraded"
    assert third["consecutiveFailures"] == 3
    assert third["lastErrorCode"] == "SOURCE_TIMEOUT"
    assert _parse_utc(third["nextFetchAt"]) - _parse_utc(third["lastFailedAt"]) == timedelta(minutes=90)
    assert third["degradedUntil"] == third["nextFetchAt"]
    assert fifth["status"] == "circuit_open"
    assert _parse_utc(fifth["nextFetchAt"]) - _parse_utc(fifth["lastFailedAt"]) == timedelta(minutes=30)
    assert fifth["degradedUntil"] is None


def test_postgres_collection_store_maps_missing_records_to_contract_errors() -> None:
    store = make_store(FakePostgresState())

    with pytest.raises(QueryServiceError) as run_exc:
        store.get_run("run_missing")
    with pytest.raises(QueryServiceError) as item_exc:
        store.get_raw_item("raw_missing")

    assert run_exc.value.code == ErrorCode.FETCH_RUN_NOT_FOUND
    assert item_exc.value.code == ErrorCode.RAW_ITEM_NOT_FOUND


def source_payload() -> dict[str, Any]:
    return {
        "id": "src_hn",
        "name": "Hacker News",
        "status": "enabled",
        "fetchIntervalMinutes": 30,
    }


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def raw_item_payload(source: dict[str, Any], *, item_id: str = "raw_first") -> dict[str, Any]:
    return {
        "id": item_id,
        "sourceId": source["id"],
        "sourceName": source["name"],
        "title": "First item",
        "url": "https://example.com/item",
        "normalizedUrl": "https://example.com/item",
        "publishedAt": "2026-05-29T00:00:00Z",
        "fetchedAt": "2026-05-29T00:00:03Z",
        "author": None,
        "summary": "Summary",
        "contentSnippet": "Snippet",
        "hotScore": None,
        "rank": 1,
        "image": None,
        "rawPayloadRef": None,
        "status": "new",
        "dedupeKey": "url:https://example.com/item",
    }


def _run_row(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": params["id"],
        "source_id": params["source_id"],
        "trigger": params["trigger"],
        "status": params["status"],
        "started_at": params["started_at"],
        "finished_at": params["finished_at"],
        "duration_ms": params["duration_ms"],
        "fetched_count": params["fetched_count"],
        "new_count": params["new_count"],
        "duplicate_count": params["duplicate_count"],
        "ignored_count": params["ignored_count"],
        "error_code": params["error_code"],
        "error_message": params["error_message"],
        "trace_id": params["trace_id"],
        "idempotency_key": params["idempotency_key"],
    }


def _run_finish_update(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": params["status"],
        "finished_at": params["finished_at"],
        "duration_ms": params["duration_ms"],
        "fetched_count": params["fetched_count"],
        "new_count": params["new_count"],
        "duplicate_count": params["duplicate_count"],
        "ignored_count": params["ignored_count"],
        "error_code": params["error_code"],
        "error_message": params["error_message"],
    }


def _raw_item_row(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": params["id"],
        "source_id": params["source_id"],
        "source_name": params["source_name"],
        "title": params["title"],
        "url": params["url"],
        "normalized_url": params["normalized_url"],
        "published_at": params["published_at"],
        "fetched_at": params["fetched_at"],
        "author": params["author"],
        "summary": params["summary"],
        "content_snippet": params["content_snippet"],
        "hot_score": params["hot_score"],
        "rank": params["rank"],
        "image": params["image"],
        "raw_payload_ref": params["raw_payload_ref"],
        "status": params["status"],
        "dedupe_key": params["dedupe_key"],
        "created_at": params["created_at"],
    }


def _health_row(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": params["source_id"],
        "status": params["status"],
        "last_succeeded_at": params["last_succeeded_at"],
        "last_failed_at": params["last_failed_at"],
        "consecutive_failures": params["consecutive_failures"],
        "next_fetch_at": params["next_fetch_at"],
        "circuit_opened_at": params["circuit_opened_at"],
        "degraded_until": params["degraded_until"],
        "last_error_code": params["last_error_code"],
        "last_error_message": params["last_error_message"],
        "updated_at": params.get("updated_at", datetime.now(timezone.utc)),
    }

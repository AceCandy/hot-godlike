from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from app.core.errors import QueryServiceError


class SchedulerService:
    def __init__(
        self,
        *,
        source_repository: Any,
        collection_store: Any,
        runner: Any,
        now_func: Callable[[], datetime] | None = None,
        take: int = 100,
    ) -> None:
        self._source_repository = source_repository
        self._collection_store = collection_store
        self._runner = runner
        self._now_func = now_func or _utc_now
        self._take = take

    async def run_due_once(self) -> dict[str, int]:
        now = _ensure_utc(self._now_func())
        sources = [
            source
            for source in self._source_repository.list(take=self._take)["items"]
            if source.get("enabled", True)
        ]
        summary = {"scanned": len(sources), "due": 0, "fetched": 0, "skipped": 0, "failed": 0}

        for source in sources:
            if not _is_due(source, self._latest_health(source["id"]), now):
                summary["skipped"] += 1
                continue
            summary["due"] += 1
            try:
                await self._runner.fetch_source(
                    source["id"],
                    idempotency_key=_schedule_idempotency_key(source["id"], now),
                    trigger="schedule",
                )
                summary["fetched"] += 1
            except QueryServiceError:
                summary["failed"] += 1

        return summary

    def _latest_health(self, source_id: str) -> dict[str, Any] | None:
        items = self._collection_store.list_health(source_id=source_id, take=1)["items"]
        return items[0] if items else None


def _is_due(source: dict[str, Any], health: dict[str, Any] | None, now: datetime) -> bool:
    next_fetch_at = _parse_time(health.get("nextFetchAt")) if health else None
    if next_fetch_at:
        return now >= next_fetch_at

    last_succeeded_at = _parse_time(health.get("lastSucceededAt")) if health else None
    last_fetched_at = _parse_time(source.get("lastFetchedAt"))
    last_at = last_succeeded_at or last_fetched_at
    if not last_at:
        return True
    return now >= last_at + _interval(source)


def _interval(source: dict[str, Any]):
    from datetime import timedelta

    return timedelta(minutes=int(source.get("fetchIntervalMinutes", 30)))


def _schedule_idempotency_key(source_id: str, now: datetime) -> str:
    return f"schedule:{source_id}:{now.strftime('%Y%m%d%H%M')}"


def _parse_time(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _ensure_utc(value)
    if isinstance(value, str):
        return _ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
    raise TypeError(f"unsupported datetime value: {value!r}")


def _ensure_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

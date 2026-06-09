from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.scheduler_worker import SchedulerWorker


@pytest.mark.asyncio
async def test_scheduler_worker_registers_interval_job_and_runs_due_once() -> None:
    service = FakeSchedulerService()
    apscheduler = FakeApscheduler()
    worker = SchedulerWorker(
        scheduler_service=service,
        interval_seconds=15,
        scheduler_factory=lambda: apscheduler,
    )

    worker.start()
    worker.start()

    assert apscheduler.started == 1
    assert len(apscheduler.jobs) == 1
    job = apscheduler.jobs[0]
    assert job["trigger"] == "interval"
    assert job["seconds"] == 15
    assert job["id"] == "collection-scheduler"
    assert job["coalesce"] is True
    assert job["max_instances"] == 1

    await job["func"]()

    assert service.calls == 1


def test_scheduler_worker_shutdown_releases_apscheduler() -> None:
    apscheduler = FakeApscheduler()
    worker = SchedulerWorker(
        scheduler_service=FakeSchedulerService(),
        scheduler_factory=lambda: apscheduler,
    )

    worker.stop()
    worker.start()
    worker.stop()
    worker.stop()

    assert apscheduler.started == 1
    assert apscheduler.shutdown_wait_values == [False]


def test_app_lifespan_keeps_scheduler_worker_disabled_by_default() -> None:
    worker = FakeLifecycleWorker()
    app = create_app(scheduler_worker=worker)

    with TestClient(app):
        assert worker.started == 0

    assert worker.stopped == 0


def test_app_lifespan_starts_and_stops_scheduler_worker_when_enabled() -> None:
    worker = FakeLifecycleWorker()
    app = create_app(
        scheduler_worker=worker,
        scheduler_worker_enabled=True,
    )

    with TestClient(app):
        assert worker.started == 1
        assert worker.stopped == 0

    assert worker.stopped == 1


class FakeSchedulerService:
    def __init__(self) -> None:
        self.calls = 0

    async def run_due_once(self) -> dict[str, int]:
        self.calls += 1
        return {"scanned": 0, "due": 0, "fetched": 0, "skipped": 0, "failed": 0}


class FakeApscheduler:
    def __init__(self) -> None:
        self.jobs: list[dict[str, Any]] = []
        self.started = 0
        self.shutdown_wait_values: list[bool] = []

    def add_job(self, func: Any, **kwargs: Any) -> None:
        self.jobs.append({"func": func, **kwargs})

    def start(self) -> None:
        self.started += 1

    def shutdown(self, *, wait: bool) -> None:
        self.shutdown_wait_values.append(wait)


class FakeLifecycleWorker:
    def __init__(self) -> None:
        self.started = 0
        self.stopped = 0

    def start(self) -> None:
        self.started += 1

    def stop(self) -> None:
        self.stopped += 1

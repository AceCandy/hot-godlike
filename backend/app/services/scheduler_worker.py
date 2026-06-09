from collections.abc import Callable
from typing import Any


class SchedulerWorker:
    def __init__(
        self,
        *,
        scheduler_service: Any,
        interval_seconds: int = 60,
        job_id: str = "collection-scheduler",
        scheduler_factory: Callable[[], Any] | None = None,
    ) -> None:
        if interval_seconds < 1:
            raise ValueError("scheduler worker interval must be at least 1 second.")
        self._scheduler_service = scheduler_service
        self._interval_seconds = interval_seconds
        self._job_id = job_id
        self._scheduler_factory = scheduler_factory or _build_apscheduler
        self._apscheduler: Any | None = None

    def start(self) -> None:
        if self._apscheduler is not None:
            return
        scheduler = self._scheduler_factory()
        # AsyncIOScheduler 可运行协程任务；服务层负责源级幂等，
        # max_instances 负责避免同一个 worker 内扫描重叠。
        scheduler.add_job(
            self._scheduler_service.run_due_once,
            trigger="interval",
            seconds=self._interval_seconds,
            id=self._job_id,
            coalesce=True,
            max_instances=1,
            replace_existing=True,
        )
        scheduler.start()
        self._apscheduler = scheduler

    def stop(self) -> None:
        if self._apscheduler is None:
            return
        self._apscheduler.shutdown(wait=False)
        self._apscheduler = None


def build_scheduler_worker(
    *, scheduler_service: Any, interval_seconds: int
) -> SchedulerWorker:
    return SchedulerWorker(
        scheduler_service=scheduler_service,
        interval_seconds=interval_seconds,
    )


def _build_apscheduler() -> Any:
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
    except ImportError as exc:
        raise RuntimeError(
            "USE_SCHEDULER_WORKER=true 时必须安装 apscheduler 依赖。"
        ) from exc
    return AsyncIOScheduler(timezone="UTC")

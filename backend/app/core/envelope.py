from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.errors import QueryServiceError

ORIGINAL_SOURCE_WARNING = "摘要由 AI HOT 生成，关键事实请打开原文核对。"


def trace_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"tr_{stamp}_{uuid4().hex[:8]}"


def success_payload(
    data: Any,
    *,
    trace: str,
    query: dict[str, Any],
    cached: bool = False,
    warnings: list[str] | None = None,
    source: str = "aihot",
) -> dict[str, Any]:
    return {
        "data": data,
        "meta": {
            "traceId": trace,
            "source": source,
            "cached": cached,
            "query": query,
            "warnings": warnings or [],
        },
        "error": None,
    }


def error_payload(
    exc: QueryServiceError,
    *,
    trace: str,
    query: dict[str, Any],
    source: str = "aihot",
) -> dict[str, Any]:
    return {
        "data": None,
        "meta": {
            "traceId": trace,
            "source": source,
            "cached": False,
            "query": query,
            "warnings": [],
        },
        "error": {
            "code": exc.code.value,
            "message": exc.message,
            "details": exc.details,
            "retryable": exc.retryable,
        },
    }

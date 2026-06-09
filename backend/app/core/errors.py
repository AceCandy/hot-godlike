from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    BAD_REQUEST = "BAD_REQUEST"
    UPSTREAM_FORBIDDEN = "UPSTREAM_FORBIDDEN"
    UPSTREAM_NOT_FOUND = "UPSTREAM_NOT_FOUND"
    UPSTREAM_RATE_LIMITED = "UPSTREAM_RATE_LIMITED"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    UPSTREAM_BAD_RESPONSE = "UPSTREAM_BAD_RESPONSE"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    SOURCE_DISABLED = "SOURCE_DISABLED"
    SOURCE_COOKIE_REQUIRED = "SOURCE_COOKIE_REQUIRED"
    SOURCE_UNREACHABLE = "SOURCE_UNREACHABLE"
    SOURCE_TIMEOUT = "SOURCE_TIMEOUT"
    SOURCE_BAD_RESPONSE = "SOURCE_BAD_RESPONSE"
    SOURCE_SSRF_BLOCKED = "SOURCE_SSRF_BLOCKED"
    SOURCE_RATE_LIMITED = "SOURCE_RATE_LIMITED"
    FETCH_RUN_NOT_FOUND = "FETCH_RUN_NOT_FOUND"
    RAW_ITEM_NOT_FOUND = "RAW_ITEM_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class QueryServiceError(Exception):
    def __init__(
        self,
        *,
        code: ErrorCode,
        message: str,
        status_code: int,
        retryable: bool,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}


def bad_request(message: str, details: dict[str, Any] | None = None) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.BAD_REQUEST,
        message=message,
        status_code=400,
        retryable=False,
        details=details,
    )


def upstream_forbidden() -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.UPSTREAM_FORBIDDEN,
        message="数据源拒绝访问，请检查 User-Agent 或数据源访问限制。",
        status_code=502,
        retryable=False,
        details={"upstreamStatus": 403},
    )


def upstream_not_found() -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.UPSTREAM_NOT_FOUND,
        message="该日期暂无日报。",
        status_code=404,
        retryable=False,
        details={"upstreamStatus": 404},
    )


def upstream_rate_limited() -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.UPSTREAM_RATE_LIMITED,
        message="数据源限流，请稍后重试。",
        status_code=503,
        retryable=True,
        details={"upstreamStatus": 429},
    )


def upstream_unavailable(
    status_code: int | None = None,
    details: dict[str, Any] | None = None,
) -> QueryServiceError:
    error_details = {"upstreamStatus": status_code}
    if details:
        error_details.update(details)
    return QueryServiceError(
        code=ErrorCode.UPSTREAM_UNAVAILABLE,
        message="数据源暂时不可用，请稍后重试。",
        status_code=503,
        retryable=True,
        details=error_details,
    )


def upstream_timeout() -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.UPSTREAM_TIMEOUT,
        message="数据源请求超时，请稍后重试。",
        status_code=504,
        retryable=True,
        details={"upstreamStatus": None},
    )


def upstream_bad_response(details: dict[str, Any] | None = None) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.UPSTREAM_BAD_RESPONSE,
        message="数据源响应异常。",
        status_code=502,
        retryable=True,
        details=details,
    )


def source_ssrf_blocked(
    message: str = "数据源 URL 被安全策略拦截。",
    details: dict[str, Any] | None = None,
) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.SOURCE_SSRF_BLOCKED,
        message=message,
        status_code=400,
        retryable=False,
        details=details,
    )


def source_not_found(source_id: str) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.SOURCE_NOT_FOUND,
        message="数据源不存在。",
        status_code=404,
        retryable=False,
        details={"sourceId": source_id},
    )


def source_disabled(source_id: str) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.SOURCE_DISABLED,
        message="数据源已停用，不能触发抓取。",
        status_code=409,
        retryable=False,
        details={"sourceId": source_id},
    )


def source_cookie_required(source_id: str | None = None) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.SOURCE_COOKIE_REQUIRED,
        message="该数据源需要 Cookie，M2 暂不执行抓取。",
        status_code=409,
        retryable=False,
        details={"sourceId": source_id},
    )


def source_rate_limited(details: dict[str, Any] | None = None) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.SOURCE_RATE_LIMITED,
        message="数据源限流，请稍后重试。",
        status_code=503,
        retryable=True,
        details=details,
    )


def fetch_run_not_found(run_id: str) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.FETCH_RUN_NOT_FOUND,
        message="抓取运行记录不存在。",
        status_code=404,
        retryable=False,
        details={"runId": run_id},
    )


def raw_item_not_found(raw_item_id: str) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.RAW_ITEM_NOT_FOUND,
        message="原始条目不存在。",
        status_code=404,
        retryable=False,
        details={"rawItemId": raw_item_id},
    )


def source_unreachable(details: dict[str, Any] | None = None) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.SOURCE_UNREACHABLE,
        message="数据源暂时不可访问，请稍后重试。",
        status_code=502,
        retryable=True,
        details=details,
    )


def source_timeout(details: dict[str, Any] | None = None) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.SOURCE_TIMEOUT,
        message="数据源抓取超时，请稍后重试。",
        status_code=504,
        retryable=True,
        details=details,
    )


def source_bad_response(details: dict[str, Any] | None = None) -> QueryServiceError:
    return QueryServiceError(
        code=ErrorCode.SOURCE_BAD_RESPONSE,
        message="数据源响应异常，无法解析。",
        status_code=502,
        retryable=True,
        details=details,
    )

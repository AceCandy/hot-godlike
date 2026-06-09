from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.errors import bad_request
from app.services.time_window import resolve_since

ALLOWED_MODES = {"selected", "all"}
ALLOWED_CATEGORIES = {"ai-models", "ai-products", "industry", "paper", "tip"}


@dataclass(frozen=True)
class QueryPlan:
    upstream_path: str
    params: dict[str, Any]
    cache_key: str
    window: dict[str, str | None]
    public_query: dict[str, Any]


def plan_items(
    *,
    mode: str = "selected",
    category: str | None = None,
    q: str | None = None,
    since: str | None = None,
    time_preset: str | None = None,
    take: int = 50,
    cursor: str | None = None,
) -> QueryPlan:
    normalized_mode = (mode or "selected").strip()
    if normalized_mode not in ALLOWED_MODES:
        raise bad_request("mode 仅支持 selected 或 all。", {"mode": mode})

    normalized_category = category.strip() if category else None
    if normalized_category and normalized_category not in ALLOWED_CATEGORIES:
        raise bad_request("category 不在支持范围内。", {"category": category})

    normalized_q = q.strip() if q else None
    if normalized_q is not None and len(normalized_q) < 2:
        raise bad_request("关键词至少 2 个字符。", {"q": q})
    if normalized_q is not None and len(normalized_q) > 200:
        raise bad_request("关键词最长 200 个字符。", {"qLength": len(normalized_q)})

    if take < 1 or take > 100:
        raise bad_request("take 必须在 1 到 100 之间。", {"take": take})

    resolved_since, window = resolve_since(since=since, time_preset=time_preset)

    params: dict[str, Any] = {"mode": normalized_mode, "take": take}
    if normalized_category:
        params["category"] = normalized_category
    if normalized_q:
        params["q"] = normalized_q
    if resolved_since:
        params["since"] = resolved_since
    if cursor:
        params["cursor"] = cursor

    public_query = {
        "mode": normalized_mode,
        "category": normalized_category,
        "q": normalized_q,
        "since": resolved_since,
        "timePreset": time_preset,
        "take": take,
        "cursor": cursor,
    }
    return QueryPlan(
        upstream_path="/api/public/items",
        params=params,
        cache_key=_cache_key("/api/public/items", params),
        window=window,
        public_query={k: v for k, v in public_query.items() if v is not None},
    )


def plan_daily(*, date: str | None = None) -> QueryPlan:
    if date:
        if not _looks_like_date(date):
            raise bad_request("date 必须使用 YYYY-MM-DD 格式。", {"date": date})
        path = f"/api/public/daily/{date}"
        public_query = {"date": date}
    else:
        path = "/api/public/daily"
        public_query = {}
    return QueryPlan(
        upstream_path=path,
        params={},
        cache_key=_cache_key(path, {}),
        window={"label": "日报", "since": None, "timezone": "Asia/Shanghai"},
        public_query=public_query,
    )


def plan_dailies(*, take: int = 30) -> QueryPlan:
    if take < 1 or take > 100:
        raise bad_request("take 必须在 1 到 100 之间。", {"take": take})
    params = {"take": take}
    return QueryPlan(
        upstream_path="/api/public/dailies",
        params=params,
        cache_key=_cache_key("/api/public/dailies", params),
        window={"label": "日报归档", "since": None, "timezone": "Asia/Shanghai"},
        public_query=params,
    )


def request_headers(etag: str | None = None) -> dict[str, str]:
    headers = {"User-Agent": settings.user_agent}
    if etag:
        headers["If-None-Match"] = etag
    return headers


def _cache_key(path: str, params: dict[str, Any]) -> str:
    pieces = [path]
    for key in sorted(params):
        pieces.append(f"{key}={params[key]}")
    return "|".join(pieces)


def _looks_like_date(value: str) -> bool:
    parts = value.split("-")
    if len(parts) != 3:
        return False
    year, month, day = parts
    return len(year) == 4 and len(month) == 2 and len(day) == 2 and all(p.isdigit() for p in parts)

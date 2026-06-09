from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from app.core.errors import bad_request
from app.services.ssrf import SSRFGuard

SourceType = Literal["aihot_api", "aihot_rss", "rss", "rsshub"]
TrustLevel = Literal["high", "medium", "low"]

SOURCE_TYPES = {"aihot_api", "aihot_rss", "rss", "rsshub"}
TRUST_LEVELS = {"high", "medium", "low"}
TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
CATEGORY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


@dataclass(frozen=True)
class SourceInput:
    name: str
    type: SourceType
    category: str
    url: str | None
    route: str | None
    enabled: bool
    fetchIntervalMinutes: int
    timeoutSeconds: int
    retryCount: int
    concurrencyLimit: int
    trustLevel: TrustLevel
    requiresCookie: bool

    def __post_init__(self) -> None:
        errors: dict[str, Any] = {}
        name = self.name.strip() if isinstance(self.name, str) else ""
        category = self.category.strip() if isinstance(self.category, str) else ""

        if not 1 <= len(name) <= 80:
            errors["name"] = "长度必须为 1-80。"
        if not CATEGORY_PATTERN.fullmatch(category):
            errors["category"] = "只允许字母、数字、短横线、下划线，长度 1-40。"
        if self.type not in SOURCE_TYPES:
            errors["type"] = "不支持的数据源类型。"
        if self.trustLevel not in TRUST_LEVELS:
            errors["trustLevel"] = "trustLevel 仅支持 high/medium/low。"
        if not 5 <= self.fetchIntervalMinutes <= 1440:
            errors["fetchIntervalMinutes"] = "范围必须为 5-1440。"
        if not 5 <= self.timeoutSeconds <= 60:
            errors["timeoutSeconds"] = "范围必须为 5-60。"
        if not 0 <= self.retryCount <= 3:
            errors["retryCount"] = "范围必须为 0-3。"
        if not 1 <= self.concurrencyLimit <= 5:
            errors["concurrencyLimit"] = "范围必须为 1-5。"

        url = self.url.strip() if isinstance(self.url, str) and self.url.strip() else None
        route = self.route.strip() if isinstance(self.route, str) and self.route.strip() else None
        if self.type in {"rss", "aihot_rss"} and not url:
            errors["url"] = "rss/aihot_rss 必须提供 url。"
        if self.type == "rsshub" and not route:
            errors["route"] = "rsshub 必须提供 route。"

        if errors:
            raise bad_request("数据源配置不符合要求。", errors)

        if url:
            SSRFGuard().validate_url(url)


def build_rsshub_feed_url(*, base_url: str, route: str, guard: SSRFGuard | None = None) -> str:
    normalized_base = base_url.rstrip("/") + "/"
    normalized_route = route.lstrip("/")
    url = urljoin(normalized_base, normalized_route)
    (guard or SSRFGuard()).validate_url(url)
    return url


def normalize_raw_item(
    *,
    source_id: str,
    source_name: str,
    raw: dict[str, Any],
    fetched_at: datetime,
) -> dict[str, Any] | None:
    title = _clean_text(raw.get("title"))
    if not title:
        return None

    url = _clean_text(raw.get("url") or raw.get("link")) or ""
    normalized_url = normalize_url(url) if url else ""
    published_at = raw.get("publishedAt") or raw.get("published_at") or raw.get("published")
    dedupe_key = _dedupe_key(title=title, normalized_url=normalized_url, published_at=published_at)
    if not dedupe_key:
        return None

    return {
        "id": f"raw_{source_id}_{_compact_key(dedupe_key)}",
        "sourceId": source_id,
        "sourceName": source_name,
        "title": title,
        "url": url,
        "normalizedUrl": normalized_url,
        "publishedAt": published_at,
        "fetchedAt": _format_utc(fetched_at),
        "author": _clean_text(raw.get("author")),
        "summary": raw.get("summary"),
        "contentSnippet": raw.get("contentSnippet") or raw.get("content_snippet"),
        "hotScore": raw.get("hotScore") or raw.get("hot_score"),
        "rank": _as_int(raw.get("rank")),
        "image": raw.get("image"),
        "rawPayloadRef": None,
        "status": "new",
        "dedupeKey": dedupe_key,
    }


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    hostname = (parsed.hostname or "").lower()
    netloc = hostname
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    path = parsed.path or "/"
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not _is_tracking_query(key)
    ]
    query = urlencode(sorted(query_pairs))
    return urlunparse((scheme, netloc, path, "", query, ""))


def _dedupe_key(*, title: str, normalized_url: str, published_at: Any) -> str | None:
    if normalized_url:
        return f"url:{normalized_url}"
    normalized_title = _slug_text(title)
    published_date = _published_date(published_at)
    if normalized_title and published_date:
        return f"title_date:{normalized_title}:{published_date}"
    return None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return re.sub(r"\s+", " ", text) if text else None


def _slug_text(value: str) -> str:
    return re.sub(r"\s+", "-", value.strip().lower())


def _published_date(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) < 10:
        return None
    return value[:10]


def _is_tracking_query(key: str) -> bool:
    normalized = key.lower()
    return normalized in TRACKING_QUERY_KEYS or normalized.startswith(TRACKING_QUERY_PREFIXES)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _format_utc(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return normalized.isoformat().replace("+00:00", "Z")


def _compact_key(value: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return compact[:48] or "item"

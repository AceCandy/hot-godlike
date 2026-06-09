from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.errors import bad_request

USER_TZ = ZoneInfo("Asia/Shanghai")
MAX_ITEMS_WINDOW = timedelta(days=7)


def parse_iso_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise bad_request("since 必须是合法 ISO 8601 时间。") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def resolve_since(
    *,
    since: str | None,
    time_preset: str | None,
    now: datetime | None = None,
) -> tuple[str | None, dict[str, str | None]]:
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    now_local = now_utc.astimezone(USER_TZ)

    if since and time_preset:
        raise bad_request("since 和 timePreset 不能同时传。")

    if since:
        since_utc = parse_iso_datetime(since)
        _validate_window(since_utc, now_utc)
        return since_utc.isoformat().replace("+00:00", "Z"), {
            "label": "自定义时间窗",
            "since": since_utc.isoformat().replace("+00:00", "Z"),
            "timezone": "Asia/Shanghai",
        }

    if not time_preset:
        return None, {"label": "默认时间窗", "since": None, "timezone": "Asia/Shanghai"}

    preset = time_preset.strip().lower()
    if preset == "today":
        local_since = datetime.combine(now_local.date(), time.min, tzinfo=USER_TZ)
        label = "今天"
    elif preset == "yesterday":
        local_since = datetime.combine(now_local.date() - timedelta(days=1), time.min, tzinfo=USER_TZ)
        label = "昨天"
    elif preset == "24h":
        local_since = now_local - timedelta(hours=24)
        label = "过去 24 小时"
    elif preset == "3d":
        local_since = now_local - timedelta(days=3)
        label = "最近 3 天"
    elif preset == "7d":
        local_since = now_local - timedelta(days=7)
        label = "最近 7 天"
    else:
        raise bad_request("timePreset 仅支持 today、yesterday、24h、3d、7d。")

    since_utc = local_since.astimezone(timezone.utc)
    _validate_window(since_utc, now_utc)
    iso_since = since_utc.isoformat().replace("+00:00", "Z")
    return iso_since, {"label": label, "since": iso_since, "timezone": "Asia/Shanghai"}


def _validate_window(since_utc: datetime, now_utc: datetime) -> None:
    if since_utc > now_utc:
        raise bad_request("since 不能是未来时间。")
    if now_utc - since_utc > MAX_ITEMS_WINDOW + timedelta(seconds=1):
        raise bad_request("items 查询最长支持最近 7 天，请使用日报归档查询更早内容。")

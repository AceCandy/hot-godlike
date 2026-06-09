from dataclasses import dataclass
import os


def _env_bool(name: str) -> bool:
    return os.getenv(name, "false").lower() == "true"


@dataclass(frozen=True)
class Settings:
    aihot_base_url: str = os.getenv("AIHOT_BASE_URL", "https://aihot.virxact.com")
    user_agent: str = os.getenv(
        "AIHOT_USER_AGENT",
        "hot-godlike-agent/0.1 (+https://github.com/local/hot-godlike)",
    )
    request_timeout_seconds: float = float(os.getenv("AIHOT_TIMEOUT_SECONDS", "10"))
    retry_count: int = int(os.getenv("AIHOT_RETRY_COUNT", "2"))
    rsshub_base_url: str = os.getenv("RSSHUB_BASE_URL", "https://rsshub.app")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    use_redis_lock: bool = _env_bool("USE_REDIS_LOCK")
    use_redis_source_metadata: bool = _env_bool("USE_REDIS_SOURCE_METADATA")
    use_redis_source_dedupe: bool = _env_bool("USE_REDIS_SOURCE_DEDUPE")
    postgres_dsn: str | None = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN")
    use_postgres_source_repository: bool = _env_bool("USE_POSTGRES_SOURCE_REPOSITORY")
    use_postgres_collection_store: bool = _env_bool("USE_POSTGRES_COLLECTION_STORE")
    use_scheduler_worker: bool = _env_bool("USE_SCHEDULER_WORKER")
    scheduler_worker_interval_seconds: int = int(
        os.getenv("SCHEDULER_WORKER_INTERVAL_SECONDS", "60")
    )


settings = Settings()

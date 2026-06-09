from typing import Any


class InMemoryCacheStore:
    """M1-only in-memory cache; replace with Redis in M2."""

    def __init__(self) -> None:
        self._etags: dict[str, str] = {}
        self._responses: dict[str, Any] = {}

    def get_etag(self, key: str) -> str | None:
        return self._etags.get(key)

    def set_etag(self, key: str, etag: str | None) -> None:
        if etag:
            self._etags[key] = etag

    def get_response(self, key: str) -> Any | None:
        return self._responses.get(key)

    def set_response(self, key: str, payload: Any) -> None:
        self._responses[key] = payload

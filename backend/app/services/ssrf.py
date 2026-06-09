from collections.abc import Callable
from ipaddress import ip_address
import socket
from urllib.parse import urlparse

from app.core.errors import source_ssrf_blocked


class SSRFGuard:
    def __init__(self, resolve_host: Callable[[str], list[str]] | None = None) -> None:
        self._resolve_host = resolve_host or _resolve_host

    def validate_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise source_ssrf_blocked(details={"reason": "unsupported_scheme", "scheme": parsed.scheme})
        if not parsed.hostname:
            raise source_ssrf_blocked(details={"reason": "missing_hostname"})

        hostname = parsed.hostname.strip().lower()
        if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".localhost"):
            raise source_ssrf_blocked(details={"reason": "localhost", "host": hostname})

        ips = [hostname] if _looks_like_ip(hostname) else self._resolve_host(hostname)
        for value in ips:
            if _is_blocked_ip(value):
                raise source_ssrf_blocked(details={"reason": "blocked_ip", "host": hostname, "ip": value})
        return url


def _resolve_host(host: str) -> list[str]:
    try:
        return sorted({result[4][0] for result in socket.getaddrinfo(host, None)})
    except socket.gaierror as exc:
        raise source_ssrf_blocked(details={"reason": "dns_resolution_failed", "host": host}) from exc


def _looks_like_ip(value: str) -> bool:
    try:
        ip_address(value)
    except ValueError:
        return False
    return True


def _is_blocked_ip(value: str) -> bool:
    try:
        parsed = ip_address(value)
    except ValueError:
        return True
    return (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_reserved
        or parsed.is_unspecified
    )

"""Block obviously unsafe URLs (SSRF mitigation for user-controlled env URLs)."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeUrlError(Exception):
    """URL is not allowed for fetching."""


def assert_fetchable_http_url(url: str) -> None:
    """Reject non-http(s) schemes and hosts that resolve only to non-public IPs."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError(f"Only http and https URLs are allowed, got scheme {parsed.scheme!r}.")
    host = parsed.hostname
    if not host:
        raise UnsafeUrlError("URL has no hostname.")
    # Reject bare hostnames that look like IPs without resolution
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        _assert_public_ip(host)

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError as e:
        raise UnsafeUrlError(f"Could not resolve host {host!r}: {e}") from e

    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise UnsafeUrlError(f"Host {host!r} resolves to a non-public address: {ip}.")


def _assert_public_ip(host: str) -> None:
    ip = ipaddress.ip_address(host)
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        raise UnsafeUrlError(f"Address {host!r} is not a public fetch target.")

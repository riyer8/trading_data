"""Lightweight connectivity checks for offline fallback."""

from __future__ import annotations

import socket

_PROBE_HOSTS = (
    ("1.1.1.1", 443),
    ("8.8.8.8", 53),
)


def is_online(timeout: float = 2.0) -> bool:
    """Return True when a basic outbound connection succeeds."""
    for host, port in _PROBE_HOSTS:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False

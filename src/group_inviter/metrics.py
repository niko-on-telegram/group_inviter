"""Prometheus metrics definitions."""

from __future__ import annotations

import logging
from threading import Lock

from prometheus_client import Counter, start_http_server

LOGGER = logging.getLogger(__name__)

_SERVER_STARTED = False
_SERVER_LOCK = Lock()

START_HANDLER_CALLS = Counter(
    "group_inviter_start_handler_calls_total",
    "Number of times the /start handler has been executed.",
    ("user_id",),
)


def start_metrics_server(host: str, port: int, *, logger: logging.Logger | None = None) -> None:
    """Expose Prometheus metrics if not already running."""

    global _SERVER_STARTED
    with _SERVER_LOCK:
        if _SERVER_STARTED:
            return
        start_http_server(port, addr=host)
        _SERVER_STARTED = True
    (logger or LOGGER).info("Metrics server listening on %s:%s", host, port)

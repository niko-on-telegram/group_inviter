"""Logging helpers."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, tzinfo
from logging import LogRecord
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .configuration import LoggingConfig

LOGGER = logging.getLogger(__name__)

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class TimezoneAwareFormatter(logging.Formatter):
    """Formatter that renders timestamps in a specific timezone."""

    def __init__(self, *, tzinfo: tzinfo, fmt: str | None = None, datefmt: str | None = None):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self._tzinfo = tzinfo

    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        dt = datetime.fromtimestamp(record.created, tz=UTC).astimezone(self._tzinfo)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


class JsonFormatter(TimezoneAwareFormatter):
    """Format log records as JSON without extra dependencies."""

    def format(self, record: LogRecord) -> str:  # pragma: no cover - formatting glue
        data = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, TIMESTAMP_FORMAT),
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=True)


def _resolve_timezone(name: str) -> tzinfo:
    if name.upper() == "UTC":
        return UTC
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        LOGGER.warning("Unknown timezone '%s', falling back to UTC", name)
        return UTC


def _make_rotating_handler(path: Path, level: int, tzinfo: tzinfo) -> logging.Handler:
    """Create a rotating file handler with unified formatting."""

    handler = RotatingFileHandler(
        path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(
        TimezoneAwareFormatter(
            tzinfo=tzinfo,
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt=TIMESTAMP_FORMAT,
        )
    )
    return handler


def configure_logging(config: LoggingConfig) -> None:
    """Configure standard library logging based on settings."""

    tzinfo = _resolve_timezone(config.timezone)
    level = getattr(logging, config.level.upper(), logging.INFO)
    handlers: list[logging.Handler] = []

    stream_handler = logging.StreamHandler()
    if config.structured:
        stream_handler.setFormatter(JsonFormatter(tzinfo=tzinfo))
    else:
        stream_handler.setFormatter(
            TimezoneAwareFormatter(
                tzinfo=tzinfo,
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt=TIMESTAMP_FORMAT,
            )
        )
    handlers.append(stream_handler)

    log_dir = config.directory
    log_dir.mkdir(parents=True, exist_ok=True)
    info_handler = _make_rotating_handler(log_dir / config.info_filename, logging.INFO, tzinfo)
    debug_handler = _make_rotating_handler(log_dir / config.debug_filename, logging.DEBUG, tzinfo)
    handlers.extend([info_handler, debug_handler])

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )

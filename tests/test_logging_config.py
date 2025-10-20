# ruff: noqa: S101
"""Tests for logging configuration helpers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from group_inviter import logging_config as logging_module


def test_resolve_timezone_direct_utc() -> None:
    assert logging_module._resolve_timezone("UTC") is UTC


def test_resolve_timezone_falls_back_on_unknown(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        tzinfo = logging_module._resolve_timezone("Mars/Colony")

    assert tzinfo is UTC
    assert "Unknown timezone" in caplog.text


def test_timestamped_log_path_preserves_nested_structure() -> None:
    base_dir = Path("logs")
    timestamp = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)

    result = logging_module._timestamped_log_path(base_dir, "nested/info.log", timestamp)

    expected = base_dir / "nested" / "info-20240102T030405+0000.log"
    assert result == expected

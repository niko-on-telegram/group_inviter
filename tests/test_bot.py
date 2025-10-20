# ruff: noqa: S101
"""Unit tests for bot helpers."""

from __future__ import annotations

import logging

from aiogram.enums import ParseMode

from group_inviter import bot as bot_module


def test_parse_mode_from_string_valid() -> None:
    result = bot_module._parse_mode_from_string("markdown")

    assert result is ParseMode.MARKDOWN


def test_parse_mode_from_string_invalid_logs_warning(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        result = bot_module._parse_mode_from_string("plain")

    assert result is ParseMode.HTML
    assert "Unknown parse mode" in caplog.text

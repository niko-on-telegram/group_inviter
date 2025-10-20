# ruff: noqa: S101
"""Tests for application bootstrap helpers."""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock

from group_inviter import main as main_module


def test_notify_admin_skips_when_chat_id_missing() -> None:
    bot = AsyncMock()

    asyncio.run(main_module._notify_admin(bot, None, "ignored"))

    assert bot.send_message.await_count == 0


def test_notify_admin_logs_warning_on_failure(caplog) -> None:
    bot = AsyncMock()
    bot.send_message.side_effect = RuntimeError("nope")

    with caplog.at_level(logging.WARNING):
        asyncio.run(main_module._notify_admin(bot, 123, "hello"))

    assert "Failed to notify admin" in caplog.text

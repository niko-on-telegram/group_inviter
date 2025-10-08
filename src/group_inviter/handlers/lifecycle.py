"""Lifecycle handlers to inform administrators about bot status."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from aiogram import Router
from aiogram.client.bot import Bot

from ._helpers import extract_config, notify_admin

LOGGER = logging.getLogger(__name__)
router = Router()


def _timestamp_label() -> str:
    """Generate an ISO-8601 timestamp with UTC offset."""

    return datetime.now(UTC).isoformat()


@router.startup()
async def notify_startup(bot: Bot, **data: Any) -> None:
    """Send a notification to the administrator when the bot starts."""

    config = extract_config(data)
    if not config:
        return

    message = f"Bot started successfully at {_timestamp_label()}."
    await notify_admin(bot, config, message, logger=LOGGER, context="startup")


@router.shutdown()
async def notify_shutdown(bot: Bot, **data: Any) -> None:
    """Send a notification to the administrator when the bot stops."""

    config = extract_config(data)
    if not config:
        return

    message = f"Bot stopped at {_timestamp_label()}."
    await notify_admin(bot, config, message, logger=LOGGER, context="shutdown")

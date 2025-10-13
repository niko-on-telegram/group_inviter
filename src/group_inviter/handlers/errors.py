"""Error handlers for dispatcher-wide exceptions."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiogram import Router
from aiogram.types import ErrorEvent

from ._helpers import extract_config, notify_admin

LOGGER = logging.getLogger(__name__)

router = Router()


@router.errors()
async def handle_unexpected_error(event: ErrorEvent) -> None:
    """Log uncaught errors and attempt to notify the administrator."""

    exception = event.exception
    if isinstance(exception, asyncio.CancelledError):
        return

    LOGGER.error(
        "Unhandled exception while processing update %s",
        repr(event.update),
        exc_info=(type(exception), exception, exception.__traceback__),
    )

    dispatcher = getattr(event, "dispatcher", None)
    workflow_data: dict[str, Any] = getattr(dispatcher, "workflow_data", {}) if dispatcher else {}
    config = extract_config(workflow_data)
    if not config:
        return

    message = (
        "Bot encountered an unexpected error.\n"
        f"{type(exception).__name__}: {exception}"
    )
    bot = getattr(event, "bot", None)
    if bot is None:
        return
    await notify_admin(
        bot,
        config,
        message,
        logger=LOGGER,
        context="error",
    )

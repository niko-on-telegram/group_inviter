"""Error handlers for dispatcher-wide exceptions."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiogram import Router
from aiogram.types import ErrorEvent

from ..configuration import AppConfig
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

    workflow_data: dict[str, Any] = getattr(event.dispatcher, "workflow_data", {})
    config = extract_config(workflow_data)
    if not config:
        return

    message = (
        "Bot encountered an unexpected error.\n"
        f"{type(exception).__name__}: {exception}"
    )
    await notify_admin(
        event.bot,
        config,
        message,
        logger=LOGGER,
        context="error",
    )

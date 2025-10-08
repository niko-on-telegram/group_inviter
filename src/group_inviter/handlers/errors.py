"""Error handlers for dispatcher-wide exceptions."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiogram import Router
from aiogram.types import ErrorEvent

from ..configuration import AppConfig

LOGGER = logging.getLogger(__name__)

router = Router()


def _extract_config(event: ErrorEvent) -> AppConfig | None:
    workflow_data: dict[str, Any] = getattr(event.dispatcher, "workflow_data", {})
    config = workflow_data.get("config")
    return config if isinstance(config, AppConfig) else None


async def _notify_admin(event: ErrorEvent, config: AppConfig, message: str) -> None:
    admin_chat_id = config.telegram.admin_chat_id
    if not admin_chat_id:
        return
    try:
        await event.bot.send_message(chat_id=admin_chat_id, text=message)
    except Exception as notify_exc:  # pragma: no cover - best-effort notification
        LOGGER.warning(
            "Failed to notify admin about error: %s",
            notify_exc,
            exc_info=(type(notify_exc), notify_exc, notify_exc.__traceback__),
        )


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

    config = _extract_config(event)
    if not config:
        return

    message = (
        "Bot encountered an unexpected error.\n"
        f"{type(exception).__name__}: {exception}"
    )
    await _notify_admin(event, config, message)

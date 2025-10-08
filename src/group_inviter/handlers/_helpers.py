"""Shared utilities for handler modules."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from aiogram import Bot

from ..configuration import AppConfig


def extract_config(source: Mapping[str, Any] | None) -> AppConfig | None:
    """Pull validated configuration from workflow data-like mappings."""

    if not source:
        return None
    config = source.get("config")
    return config if isinstance(config, AppConfig) else None


async def notify_admin(
    bot: Bot,
    config: AppConfig,
    message: str,
    *,
    logger: logging.Logger,
    context: str,
) -> None:
    """Send a best-effort notification to the configured administrator."""

    admin_chat_id = config.telegram.admin_chat_id
    if not admin_chat_id:
        return
    try:
        await bot.send_message(chat_id=admin_chat_id, text=message)
    except Exception as notify_exc:  # pragma: no cover - best-effort notification
        logger.warning(
            "Failed to notify admin about %s: %s",
            context,
            notify_exc,
            exc_info=(type(notify_exc), notify_exc, notify_exc.__traceback__),
        )

"""Application bootstrap."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot

from .bot import create_bot, create_dispatcher
from .configuration import load_config
from .database import UsersRepository, create_pool, ensure_schema
from .logging_config import configure_logging
from .metrics import start_metrics_server

LOGGER = logging.getLogger(__name__)


async def _notify_admin(bot: Bot, chat_id: int | None, message: str) -> None:
    if not chat_id:
        return
    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as notify_exc:  # pragma: no cover - best-effort notification
        LOGGER.warning(
            "Failed to notify admin about startup/shutdown error: %s",
            notify_exc,
            exc_info=(type(notify_exc), notify_exc, notify_exc.__traceback__),
        )


async def _run_async(config_path: Path | None = None) -> None:
    config = load_config(config_path)
    configure_logging(config.logging)
    if config.metrics.enabled:
        start_metrics_server(config.metrics.host, config.metrics.port, logger=LOGGER)

    bot = create_bot(config)
    dispatcher = create_dispatcher()
    dispatcher.workflow_data.update({"config": config})

    pool = None
    try:
        pool = await create_pool(config.database)
        await ensure_schema(pool)
        dispatcher.workflow_data.update({"user_repository": UsersRepository(pool)})
        LOGGER.info("Starting polling")
        await dispatcher.start_polling(bot)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        LOGGER.error(
            "Bot runtime stopped due to an exception",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        await _notify_admin(
            bot,
            config.telegram.admin_chat_id,
            f"Bot runtime stopped due to an error:\n{type(exc).__name__}: {exc}",
        )
        raise
    finally:
        if pool is not None:
            await pool.close()
        await bot.session.close()


def main(config_path: str | None = None) -> None:
    """Entrypoint for synchronous execution."""

    try:
        asyncio.run(_run_async(Path(config_path) if config_path else None))
    except KeyboardInterrupt:  # pragma: no cover - CLI nicety
        LOGGER.info("Bot stopped via keyboard interrupt")


def entrypoint() -> None:
    """Console script wrapper expected by pyproject."""

    main()

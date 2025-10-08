"""Bot factories and lifecycle helpers."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .configuration import AppConfig
from .handlers import register

LOGGER = logging.getLogger(__name__)


def _parse_mode_from_string(parse_mode: str) -> ParseMode | None:
    try:
        return ParseMode[parse_mode.upper()]
    except KeyError:  # pragma: no cover - configuration errors
        LOGGER.warning("Unknown parse mode '%s', falling back to HTML", parse_mode)
        return ParseMode.HTML


def create_bot(config: AppConfig) -> Bot:
    """Build an aiogram Bot instance using configuration."""

    default_properties = DefaultBotProperties(
        parse_mode=_parse_mode_from_string(config.telegram.parse_mode),
    )
    return Bot(token=config.telegram.bot_token, default=default_properties)


def create_dispatcher() -> Dispatcher:
    """Create dispatcher and register routers."""

    dispatcher = Dispatcher()
    register(dispatcher)
    return dispatcher

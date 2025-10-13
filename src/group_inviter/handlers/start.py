"""/start command handler."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from ..metrics import START_HANDLER_CALLS

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Greet the user when /start is received."""

    user_id = message.from_user.id if message.from_user and message.from_user.id else "unknown"
    START_HANDLER_CALLS.labels(user_id=str(user_id)).inc()
    await message.answer(
        "👋 Привет! Я готов помочь тебе управлять приглашениями в группы. \n\n"
        "👨‍💻 by @mr_baloo"
    )

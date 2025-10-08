"""/start command handler."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Greet the user when /start is received."""

    await message.answer(
        "Hello! I'm ready to help you manage group invitations. "
        "Configure me and extend handlers in src/group_inviter/handlers."
    )

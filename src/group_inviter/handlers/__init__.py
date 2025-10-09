"""Message handlers for the bot."""

from __future__ import annotations

from aiogram import Dispatcher

from . import errors, invite, lifecycle, start

__all__ = ["register"]


def register(dp: Dispatcher) -> None:
    """Attach all routers to the dispatcher."""

    dp.include_router(errors.router)
    dp.include_router(invite.router)
    dp.include_router(lifecycle.router)
    dp.include_router(start.router)

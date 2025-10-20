"""Handlers for invite link management and join requests."""

from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Bot, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import ChatInviteLink, ChatJoinRequest, Message
from aiogram.utils.text_decorations import html_decoration as html

from ..configuration import AppConfig
from ..database import UsersRepository
from ..metrics import record_join_request_approval
from ._helpers import notify_admin

LOGGER = logging.getLogger(__name__)
router = Router()


def _is_admin(message: Message, config: AppConfig) -> bool:
    admin_id = config.telegram.admin_chat_id
    return bool(admin_id and message.from_user and message.from_user.id == admin_id)


def _format_invite_message(invite: ChatInviteLink) -> str:
    name = invite.name or datetime.now().isoformat(timespec="seconds")
    return (
        "Создана новая пригласительная ссылка:\n"
        f"{html.quote(invite.invite_link)}\n"
        f"Название: {html.quote(name)}"
    )


def _is_bot_generated_invite(invite: ChatInviteLink | None) -> bool:
    return bool(invite and invite.creator and invite.creator.is_bot)


def _welcome_message(join_request: ChatJoinRequest) -> str:
    user = join_request.from_user
    lines = [
        f"Привет, {html.quote(user.full_name)}!",
        "Твоя заявка одобрена. Добро пожаловать в чат!",
    ]
    if user.username:
        lines.append(f"Твой ник: @{html.quote(user.username)}")
    return "\n".join(lines)


async def _notify_user_of_approval(bot: Bot, join_request: ChatJoinRequest) -> None:
    """Best-effort delivery of the welcome message to the user."""

    message_text = _welcome_message(join_request)
    user_id = join_request.from_user.id
    targets: list[int] = []

    user_chat_id = getattr(join_request, "user_chat_id", None)
    if user_chat_id:
        targets.append(user_chat_id)
    if not targets or targets[-1] != user_id:
        targets.append(user_id)

    for target in targets:
        try:
            await bot.send_message(target, message_text, parse_mode="HTML")
            return
        except Exception as exc:  # pragma: no cover - depends on user privacy settings
            LOGGER.debug(
                "Failed to deliver welcome message via chat %s for user %s: %s",
                target,
                user_id,
                exc,
            )


@router.message(Command("generate_invite"))
async def handle_generate_invite(
    message: Message,
    bot: Bot,
    config: AppConfig,
    command: CommandObject,
) -> None:
    """Allow administrator to generate invite links that require approval."""

    if not _is_admin(message, config):
        await message.answer("Эта команда доступна только администратору.")
        return

    if message.chat.type != ChatType.PRIVATE:
        await message.answer("Создавать ссылки можно только из приватного чата с ботом.")
        return

    if not command.args:
        await message.answer("Укажите ID чата: /generate_invite <chat_id>.")
        return

    try:
        target_chat_id = int(command.args.strip())
    except ValueError:
        await message.answer("Некорректный ID чата. Используйте числовой идентификатор.")
        return

    try:
        invite = await bot.create_chat_invite_link(
            chat_id=target_chat_id,
            creates_join_request=True,
            name=f"Bot invite {datetime.now().isoformat(timespec='seconds')}",
        )
    except Exception as exc:  # pragma: no cover - network errors
        LOGGER.warning("Failed to create invite link: %s", exc)
        await message.answer("Не удалось создать ссылку. Убедитесь, что бот имеет права администратора.")
        return

    await message.answer(_format_invite_message(invite), parse_mode="HTML")


@router.chat_join_request()
async def handle_join_request(
    join_request: ChatJoinRequest,
    bot: Bot,
    config: AppConfig,
    user_repository: UsersRepository,
) -> None:
    """Automatically approve join requests for links created by the bot."""

    invite = join_request.invite_link
    if not _is_bot_generated_invite(invite):
        LOGGER.debug(
            "Ignoring join request from %s (%s) for chat %s via external link",
            join_request.from_user.id,
            join_request.from_user.full_name,
            join_request.chat.id,
        )
        return

    await _notify_user_of_approval(bot, join_request)

    try:
        await bot.approve_chat_join_request(join_request.chat.id, join_request.from_user.id)
    except Exception as exc:  # pragma: no cover - network errors
        LOGGER.warning(
            "Failed to approve join request from %s: %s",
            join_request.from_user.id,
            exc,
        )
        return

    try:
        await user_repository.record_join_request(join_request)
    except Exception as exc:  # pragma: no cover - database errors
        LOGGER.warning(
            "Failed to persist join request for %s: %s",
            join_request.from_user.id,
            exc,
        )

    record_join_request_approval(join_request.from_user.id)

    LOGGER.info(
        "Approved join request from %s (%s) for chat %s",
        join_request.from_user.id,
        join_request.from_user.full_name,
        join_request.chat.id,
    )

    if config:
        await notify_admin(
            bot,
            config,
            (
                "Новый участник одобрен.\n"
                f"Пользователь: {join_request.from_user.full_name} (@{join_request.from_user.username or 'нет'})"
            ),
            logger=LOGGER,
            context="join-request",
        )

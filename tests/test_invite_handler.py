# ruff: noqa: S101
"""Tests for invite handler utilities."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from aiogram.types import Chat, ChatInviteLink, ChatJoinRequest, User

from group_inviter.handlers import invite as invite_handler


def _build_join_request(*, user_id: int = 42, user_chat_id: int = 999) -> ChatJoinRequest:
    """Helper to create a minimal, valid join request object for tests."""

    return ChatJoinRequest(
        chat=Chat(id=-100500, type="supergroup"),
        from_user=User(id=user_id, is_bot=False, first_name="Tester"),
        user_chat_id=user_chat_id,
        date=datetime.now(UTC),
    )


def test_is_bot_generated_invite_recognises_bot_creator() -> None:
    invite = ChatInviteLink(
        invite_link="https://t.me/+example",
        creator=User(id=1, is_bot=True, first_name="Bot"),
        creates_join_request=True,
        is_primary=False,
        is_revoked=False,
    )

    assert invite_handler._is_bot_generated_invite(invite) is True


def test_is_bot_generated_invite_rejects_non_bot() -> None:
    invite = ChatInviteLink(
        invite_link="https://t.me/+example",
        creator=User(id=1, is_bot=False, first_name="Human"),
        creates_join_request=True,
        is_primary=False,
        is_revoked=False,
    )

    assert invite_handler._is_bot_generated_invite(invite) is False


def test_notify_user_prefers_user_chat_id() -> None:
    bot = AsyncMock()
    join_request = _build_join_request(user_id=7, user_chat_id=555)
    expected_text = invite_handler._welcome_message(join_request)

    asyncio.run(invite_handler._notify_user_of_approval(bot, join_request))

    assert bot.send_message.await_count == 1
    await_args = bot.send_message.await_args
    assert await_args.args[0] == 555
    assert await_args.args[1] == expected_text
    assert await_args.kwargs == {"parse_mode": "HTML"}


def test_notify_user_falls_back_to_user_id_when_needed() -> None:
    bot = AsyncMock()
    bot.send_message.side_effect = [RuntimeError("fail"), None]
    join_request = _build_join_request(user_id=77, user_chat_id=888)

    asyncio.run(invite_handler._notify_user_of_approval(bot, join_request))

    assert bot.send_message.await_count == 2
    first_call = bot.send_message.await_args_list[0]
    second_call = bot.send_message.await_args_list[1]

    assert first_call.args[0] == 888
    assert first_call.kwargs == {"parse_mode": "HTML"}
    assert second_call.args[0] == 77
    assert second_call.kwargs == {"parse_mode": "HTML"}

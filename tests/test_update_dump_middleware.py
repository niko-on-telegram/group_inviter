# ruff: noqa: S101
"""Tests for update dump middleware behaviour."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from aiogram.dispatcher.event.bases import UNHANDLED

from group_inviter.middlewares.update_dump import UpdateDumpMiddleware


class _Event:
    """Simple stand-in for TelegramObject supporting model_dump."""

    def __init__(self, payload: dict[str, str]) -> None:
        self._payload = payload

    def model_dump(self, *, mode: str, exclude_none: bool) -> dict[str, str]:
        assert mode == "json"
        assert exclude_none is True
        return self._payload


class _EventWithoutDump:
    """Fallback event lacking model_dump method."""

    def __repr__(self) -> str:
        return "_EventWithoutDump()"


def test_middleware_serializes_and_respects_handler_result() -> None:
    middleware = UpdateDumpMiddleware()
    handler = AsyncMock(return_value="processed")
    event = _Event({"foo": "bar"})

    with patch(
        "group_inviter.middlewares.update_dump.record_unhandled_update"
    ) as record_unhandled:
        asyncio.run(middleware(handler, event, {}))

    assert handler.await_count == 1
    assert record_unhandled.called is False


def test_middleware_tracks_unhandled_results() -> None:
    middleware = UpdateDumpMiddleware()
    handler = AsyncMock(return_value=UNHANDLED)
    event = _Event({"foo": "bar"})

    with patch(
        "group_inviter.middlewares.update_dump.record_unhandled_update"
    ) as record_unhandled:
        asyncio.run(middleware(handler, event, {}))

    assert handler.await_count == 1
    record_unhandled.assert_called_once_with()


def test_middleware_handles_objects_without_model_dump() -> None:
    middleware = UpdateDumpMiddleware()
    handler = AsyncMock(return_value="ok")
    event = _EventWithoutDump()

    asyncio.run(middleware(handler, event, {}))

    assert handler.await_count == 1

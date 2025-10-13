"""Middleware that logs incoming user updates as JSON."""

from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable

from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject

from ..metrics import record_unhandled_update

LOGGER = logging.getLogger(__name__)


class UpdateDumpMiddleware(BaseMiddleware):
    """Dump updates for messages and callback queries."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        LOGGER.info("Incoming %s: %s", event.__class__.__name__, self._serialize(event))
        result = await handler(event, data)
        if result is UNHANDLED:
            LOGGER.info("Unhandled")
            record_unhandled_update()
        return result

    @staticmethod
    def _serialize(event: TelegramObject) -> str:
        """Serialize incoming event to JSON string."""

        payload: Any
        if hasattr(event, "model_dump"):
            payload = event.model_dump(mode="json", exclude_none=True)
        else:  # pragma: no cover - fallback for unexpected types
            payload = repr(event)
        try:
            return json.dumps(payload, ensure_ascii=True)
        except TypeError:  # pragma: no cover - fallback for non-serializable payloads
            return json.dumps(str(payload), ensure_ascii=True)

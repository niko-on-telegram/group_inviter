"""Database utilities and repositories."""

from __future__ import annotations

from datetime import UTC, datetime

import asyncpg  # type: ignore[import-untyped]
from aiogram.types import ChatJoinRequest

from .configuration import DatabaseConfig


async def create_pool(config: DatabaseConfig) -> asyncpg.Pool:
    """Create an asyncpg connection pool based on validated settings."""

    return await asyncpg.create_pool(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        min_size=config.min_pool_size,
        max_size=config.max_pool_size,
    )


async def ensure_schema(pool: asyncpg.Pool) -> None:
    """Ensure that required database tables are created."""

    async with pool.acquire() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                phone_number TEXT,
                language_code TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                is_bot BOOLEAN NOT NULL DEFAULT FALSE,
                joined_chat_id BIGINT,
                user_chat_id BIGINT,
                joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_users_joined_chat_id
                ON users (joined_chat_id)
            """
        )


class UsersRepository:
    """Persistence layer for Telegram user information."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def record_join_request(self, join_request: ChatJoinRequest) -> None:
        """Upsert user details whenever a join request is approved."""

        user = join_request.from_user
        if user is None:  # pragma: no cover - defensive guard
            return

        timestamp = datetime.now(UTC)
        phone_number = getattr(user, "phone_number", None)

        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO users (
                    telegram_id,
                    first_name,
                    last_name,
                    username,
                    phone_number,
                    language_code,
                    is_premium,
                    is_bot,
                    joined_chat_id,
                    user_chat_id,
                    joined_at,
                    updated_at
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $11
                )
                ON CONFLICT (telegram_id) DO UPDATE
                SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    username = EXCLUDED.username,
                    phone_number = EXCLUDED.phone_number,
                    language_code = EXCLUDED.language_code,
                    is_premium = EXCLUDED.is_premium,
                    is_bot = EXCLUDED.is_bot,
                    joined_chat_id = EXCLUDED.joined_chat_id,
                    user_chat_id = EXCLUDED.user_chat_id,
                    updated_at = EXCLUDED.updated_at
                """,
                user.id,
                user.first_name,
                user.last_name,
                user.username,
                phone_number,
                user.language_code,
                bool(getattr(user, "is_premium", False)),
                bool(getattr(user, "is_bot", False)),
                join_request.chat.id,
                join_request.user_chat_id,
                timestamp,
            )

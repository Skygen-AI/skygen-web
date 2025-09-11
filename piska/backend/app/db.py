from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine: AsyncEngine = create_async_engine(
    settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def lifespan_session() -> AsyncIterator[AsyncSession]:
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


async def get_db() -> AsyncIterator[AsyncSession]:
    async with lifespan_session() as session:
        yield session


async def init_models() -> None:
    # retry a few times to handle startup races in containerized envs
    last_err: Exception | None = None
    for _ in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # Best-effort dev-safe migrations for existing Postgres DBs
                if conn.engine.dialect.name == "postgresql":
                    await conn.execute(
                        text(
                            "ALTER TABLE devices ADD COLUMN IF NOT EXISTS device_token_kid VARCHAR(32)"
                        )
                    )
                    await conn.execute(
                        text(
                            "ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP NULL"
                        )
                    )
                    await conn.execute(
                        text(
                            "ALTER TABLE devices ADD COLUMN IF NOT EXISTS connection_status VARCHAR(16) DEFAULT 'offline'"
                        )
                    )
                    await conn.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"
                        )
                    )
                    await conn.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE"
                        )
                    )
                    await conn.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(255)"
                        )
                    )
                    await conn.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}'"
                        )
                    )
                    await conn.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
                        )
                    )
                    # Fix timezone issues in existing tables
                    await conn.execute(
                        text(
                            "ALTER TABLE tasks ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE"
                        )
                    )
                    await conn.execute(
                        text(
                            "ALTER TABLE tasks ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE"
                        )
                    )
                    # Add new tables for advanced features
                    await conn.execute(
                        text("""
                            CREATE TABLE IF NOT EXISTS task_templates (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                                name VARCHAR(255) NOT NULL,
                                description TEXT,
                                category VARCHAR(100) DEFAULT 'general',
                                actions JSONB NOT NULL,
                                variables JSONB DEFAULT '{}',
                                is_public BOOLEAN DEFAULT FALSE,
                                usage_count INTEGER DEFAULT 0,
                                created_at TIMESTAMP DEFAULT NOW(),
                                updated_at TIMESTAMP DEFAULT NOW()
                            )
                        """)
                    )
                    await conn.execute(
                        text("""
                            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                                device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
                                template_id UUID REFERENCES task_templates(id) ON DELETE SET NULL,
                                name VARCHAR(255) NOT NULL,
                                cron_expression VARCHAR(100) NOT NULL,
                                actions JSONB NOT NULL,
                                is_active BOOLEAN DEFAULT TRUE,
                                last_run TIMESTAMP,
                                next_run TIMESTAMP,
                                run_count INTEGER DEFAULT 0,
                                created_at TIMESTAMP DEFAULT NOW()
                            )
                        """)
                    )
                    await conn.execute(
                        text(
                            "ALTER TABLE idempotency_keys ALTER COLUMN resource_id DROP NOT NULL")
                    )
            return
        except Exception as e:  # noqa: BLE001
            last_err = e
            await asyncio.sleep(1)
    if last_err:
        raise last_err


async def reset_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

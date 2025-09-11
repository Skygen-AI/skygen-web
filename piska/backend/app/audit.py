from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from app.clients import get_clickhouse


_audit_initialized = False


async def init_audit() -> None:
    global _audit_initialized
    if _audit_initialized:
        return
    client = get_clickhouse()
    if client is None:
        return
    client.command(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            ts DateTime DEFAULT now(),
            action String,
            actor_id String,
            subject_id String,
            metadata String
        ) ENGINE = MergeTree() ORDER BY ts
        """
    )
    _audit_initialized = True


async def log_event(
    action: str, actor_id: str, subject_id: str, metadata: dict[str, Any] | None = None
) -> None:
    logger.info(
        f"audit action={action} actor={actor_id} subject={subject_id} meta={metadata}")
    client = get_clickhouse()
    if client is None:
        return
    rows = [
        (
            datetime.utcnow(),
            action,
            actor_id,
            subject_id,
            str(metadata or {}),
        )
    ]
    client.insert(
        "audit_logs", rows, column_names=["ts", "action", "actor_id", "subject_id", "metadata"]
    )

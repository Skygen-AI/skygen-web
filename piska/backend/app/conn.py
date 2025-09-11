from __future__ import annotations

import asyncio
from typing import Dict, Optional

from fastapi import WebSocket


_connections: Dict[str, WebSocket] = {}
_conn_lock = asyncio.Lock()


async def register_connection(device_id: str, websocket: WebSocket) -> None:
    from loguru import logger
    async with _conn_lock:
        old = _connections.get(device_id)
        if old is not None and old is not websocket:
            # Close old connection before registering new one
            try:
                if old.client_state.name == "CONNECTED":
                    logger.info(f"Closing old connection for device {device_id}")
                    await old.close(code=4000, reason="New connection established")
            except Exception as e:
                logger.warning(f"Failed to close old connection for device {device_id}: {e}")
        _connections[device_id] = websocket
        logger.info(f"Registered WebSocket connection for device {device_id}. Total connections: {len(_connections)}")


async def remove_connection(device_id: str, websocket: WebSocket) -> None:
    from loguru import logger
    async with _conn_lock:
        if _connections.get(device_id) is websocket:
            _connections.pop(device_id, None)
            logger.info(f"Removed WebSocket connection for device {device_id}. Total connections: {len(_connections)}")


async def get_connection(device_id: str) -> Optional[WebSocket]:
    async with _conn_lock:
        return _connections.get(device_id)

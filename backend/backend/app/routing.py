from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from app.clients import get_redis
from app.config import settings
from app.conn import get_connection


ROUTE_TTL_SECONDS = 120


async def set_route(device_id: str, connection_id: str) -> None:
    redis = get_redis()
    if redis is None:
        logger.warning(f"Redis not available, cannot set route for device {device_id}")
        return
    
    key = f"route:device:{device_id}"
    route_data = {
        "device_id": device_id,
        "connection_id": connection_id,
        "node_id": settings.node_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    try:
        await redis.hset(key, mapping=route_data)
        await redis.expire(key, ROUTE_TTL_SECONDS)
        logger.info(f"Set route for device {device_id}: {route_data}")
    except Exception as e:
        logger.error(f"Failed to set route for device {device_id}: {e}")


async def clear_route(device_id: str, connection_id: str | None = None) -> None:
    redis = get_redis()
    if redis is None:
        return
    key = f"route:device:{device_id}"
    if connection_id:
        cur = await redis.hget(key, "connection_id")
        if cur and cur != connection_id:
            return
        # Only clear if this is the same connection
        await redis.delete(key)
    else:
        # If no connection_id provided, clear anyway
        await redis.delete(key)


async def publish_task_envelope(device_id: str, envelope: dict[str, Any]) -> None:
    redis = get_redis()
    if redis is None:
        logger.warning("Redis not available for task delivery")
        return
    channel = f"deliver:task:{device_id}"
    logger.info(f"Publishing task {envelope.get('task_id')} to channel {channel}")
    await redis.publish(channel, json.dumps(envelope))
    
    # Fallback: try direct delivery if device is connected on this node
    try:
        ws = await get_connection(device_id)
        if ws is not None:
            logger.info(f"Attempting direct delivery of task {envelope.get('task_id')} to device {device_id}")
            import json as json_lib
            await ws.send_text(json_lib.dumps(envelope))
            logger.info(f"Successfully delivered task {envelope.get('task_id')} directly to device {device_id}")
    except Exception as e:
        logger.warning(f"Direct delivery failed for task {envelope.get('task_id')} to device {device_id}: {e}")


async def start_delivery_subscriber() -> None:
    redis = get_redis()
    if redis is None:
        logger.warning("Redis not configured; delivery subscriber disabled")
        return
    pubsub = redis.pubsub()
    pattern = "deliver:task:*"
    await pubsub.psubscribe(pattern)
    logger.info(f"Subscribed to delivery pattern: {pattern}")
    try:
        async for msg in pubsub.listen():  # type: ignore[attr-defined]
            try:
                if msg.get("type") not in ("pmessage", "message"):
                    continue
                channel = msg.get("channel") or msg.get("pattern")
                data = msg.get("data")
                if isinstance(data, bytes):
                    data = data.decode()
                envelope = json.loads(data)
                # extract device_id from channel name deliver:task:{device_id}
                if isinstance(channel, bytes):
                    channel = channel.decode()
                parts = str(channel).split(":")
                device_id = parts[-1] if parts else envelope.get("device_id")
                if not device_id:
                    continue
                # check routing ownership
                key = f"route:device:{device_id}"
                route = await redis.hgetall(key)
                logger.info(
                    f"Delivery attempt for device {device_id}, route: {route}, current node: {settings.node_id}"
                )
                if not route or route.get("node_id") != settings.node_id:
                    logger.warning(
                        f"Route not found or not owned by this node for device {device_id}, attempting direct delivery"
                    )
                    # Try direct delivery anyway
                    ws = await get_connection(device_id)
                    if ws is not None:
                        try:
                            logger.info(f"Direct delivery attempt for task {envelope.get('task_id')} to device {device_id}")
                            await ws.send_text(json.dumps(envelope))
                            logger.info(f"Direct delivery successful for task {envelope.get('task_id')} to device {device_id}")
                            continue
                        except Exception as e:
                            logger.warning(f"Direct delivery failed for task {envelope.get('task_id')} to device {device_id}: {e}")
                    else:
                        logger.warning(f"No WebSocket connection found for device {device_id}")
                    continue
                ws = await get_connection(device_id)
                if ws is None:
                    logger.warning(f"No WebSocket connection found for device {device_id}")
                    continue
                try:
                    logger.info(f"Delivering task {envelope.get('task_id')} to device {device_id}")
                    await ws.send_text(json.dumps(envelope))
                except Exception as e:
                    logger.warning(f"Failed to deliver task to device {device_id}: {e}")
                    # Remove dead connection
                    from app.conn import remove_connection

                    await remove_connection(device_id, ws)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Delivery subscriber error: {e}")
                await asyncio.sleep(0)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Delivery subscriber stopped: {e}")

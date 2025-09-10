from __future__ import annotations

import asyncio
from typing import Optional
from datetime import datetime, timezone
import json
import uuid
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status

from app.security import is_jti_revoked, verify_device_token, verify_message_hmac, sign_message_hmac
from app.audit import log_event
from app.clients import get_redis, publish_event
from app.config import settings
from app.db import AsyncSessionLocal
from app.models import Device, Task
from app.conn import register_connection, remove_connection, get_connection
from app.routing import set_route, clear_route
from sqlalchemy import select
from loguru import logger
from app.metrics import (
    ws_connections_total,
    ws_connections_current,
    ws_heartbeats_total,
)


router = APIRouter()


PRESENCE_TTL_SECONDS = 120

# Rate limiting for WebSocket connections
_connection_attempts = {}
_blocked_devices = {}  # Temporarily blocked devices
_blocked_ips = {}  # Temporarily blocked IP addresses
_rate_limit_lock = asyncio.Lock()
MAX_CONNECTIONS_PER_MINUTE = 30  # Increased from 5 to 30 for legitimate clients
RATE_LIMIT_WINDOW = 60  # seconds
BLOCK_DURATION = 60  # Reduced from 5 minutes to 1 minute for device blocks
MAX_RATE_LIMIT_VIOLATIONS = 10  # Increased from 3 to 10 violations before blocking
IP_BLOCK_DURATION = 300  # Reduced from 10 minutes to 5 minutes for IP blocks


async def check_ip_block(client_ip: str) -> tuple[bool, str]:
    """Check if IP is temporarily blocked"""
    current_time = time.time()

    async with _rate_limit_lock:
        if client_ip in _blocked_ips:
            block_info = _blocked_ips[client_ip]
            if current_time < block_info["blocked_until"]:
                remaining = int(block_info["blocked_until"] - current_time)
                return False, f"IP blocked for {remaining} more seconds"
            else:
                # Block expired, remove it
                del _blocked_ips[client_ip]

    return True, "Allowed"


async def block_ip_for_spam(client_ip: str, device_id: str) -> None:
    """Block an IP address for excessive connection spam"""
    # Skip blocking localhost
    if client_ip in ["127.0.0.1", "localhost", "::1"]:
        logger.info(f"Skipping IP block for localhost: {client_ip}")
        return

    current_time = time.time()

    async with _rate_limit_lock:
        _blocked_ips[client_ip] = {
            "blocked_until": current_time + IP_BLOCK_DURATION,
            "reason": f"Excessive connection spam from device {device_id}",
            "device_id": device_id
        }

    logger.error(
        f"IP {client_ip} blocked for {IP_BLOCK_DURATION} seconds due to excessive spam from device {device_id}")


async def clear_all_blocks() -> dict:
    """Clear all IP and device blocks - useful for development/testing"""
    async with _rate_limit_lock:
        ip_count = len(_blocked_ips)
        device_count = len(_blocked_devices)
        connection_count = len(_connection_attempts)

        _blocked_ips.clear()
        _blocked_devices.clear()
        _connection_attempts.clear()

        logger.info(
            f"Cleared {ip_count} IP blocks, {device_count} device blocks, and {connection_count} connection attempts")

        return {
            "cleared_ip_blocks": ip_count,
            "cleared_device_blocks": device_count,
            "cleared_connection_attempts": connection_count
        }


async def check_connection_rate_limit(device_id: str) -> tuple[bool, str]:
    """Check if device has exceeded connection rate limit

    Returns:
        tuple[bool, str]: (is_allowed, reason)
    """
    current_time = time.time()

    async with _rate_limit_lock:
        # Check if device is temporarily blocked
        if device_id in _blocked_devices:
            block_info = _blocked_devices[device_id]
            if current_time < block_info["blocked_until"]:
                remaining = int(block_info["blocked_until"] - current_time)
                return False, f"Device blocked for {remaining} more seconds"
            else:
                # Block expired, remove it
                del _blocked_devices[device_id]

        if device_id not in _connection_attempts:
            _connection_attempts[device_id] = {"attempts": [], "violations": 0}

        # Clean old attempts
        _connection_attempts[device_id]["attempts"] = [
            attempt_time for attempt_time in _connection_attempts[device_id]["attempts"]
            if current_time - attempt_time < RATE_LIMIT_WINDOW
        ]

        # Check if we're at the limit
        if len(_connection_attempts[device_id]["attempts"]) >= MAX_CONNECTIONS_PER_MINUTE:
            # Increment violation count
            _connection_attempts[device_id]["violations"] += 1

            # Block device if too many violations
            if _connection_attempts[device_id]["violations"] >= MAX_RATE_LIMIT_VIOLATIONS:
                _blocked_devices[device_id] = {
                    "blocked_until": current_time + BLOCK_DURATION,
                    "reason": "Too many rate limit violations"
                }
                logger.warning(
                    f"Device {device_id} blocked for {BLOCK_DURATION} seconds due to excessive reconnection attempts")
                return False, f"Device blocked for {BLOCK_DURATION} seconds"

            return False, "Rate limit exceeded"

        # Add current attempt
        _connection_attempts[device_id]["attempts"].append(current_time)
        return True, "Allowed"


@router.websocket("/ws/agent")
async def agent_ws(websocket: WebSocket) -> None:
    client_ip = str(websocket.client.host) if websocket.client else "unknown"
    logger.info(f"WebSocket connection attempt from {websocket.client}")

    # Skip blocking checks for localhost/development
    is_localhost = client_ip in ["127.0.0.1", "localhost", "::1"]

    if not is_localhost:
        # First check if IP is blocked
        is_ip_allowed, ip_reason = await check_ip_block(client_ip)
        if not is_ip_allowed:
            logger.warning(
                f"Rejecting connection from blocked IP {client_ip}: {ip_reason}")
            await websocket.close(code=4429, reason=ip_reason)
            return

    # Accept connection first to avoid HTTP 403
    await websocket.accept()

    # Quick pre-check for blocked devices after accepting connection
    token: Optional[str] = websocket.query_params.get("token")
    device_id = None
    if token and not is_localhost:  # Skip device blocking for localhost
        try:
            # Quick token decode to get device_id for pre-check
            import jwt
            payload = jwt.decode(token, options={"verify_signature": False})
            device_id = str(payload.get("device_id"))

            # Quick block check without full rate limit logic
            current_time = time.time()
            if device_id in _blocked_devices:
                block_info = _blocked_devices[device_id]
                if current_time < block_info["blocked_until"]:
                    logger.warning(
                        f"Device {device_id} is temporarily blocked")
                    await websocket.close(code=4429, reason="Device temporarily blocked")
                    return
        except Exception:
            pass  # Continue with normal flow if pre-check fails

    if not token:
        token = websocket.query_params.get("token")
    logger.info(
        f"Token from query params: {'present' if token else 'missing'}")

    if token is None and "authorization" in websocket.headers:
        auth = websocket.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
            logger.info("Token extracted from Authorization header")

    if token is None:
        logger.error("No token provided")
        await websocket.close(code=4001)
        return

    try:
        logger.info("Attempting to verify device token...")
        payload = verify_device_token(token)
        logger.info(
            f"Token verified successfully for device: {payload.get('device_id')}")
    except Exception as e:
        # Invalid token -> close after accept
        logger.error(f"Invalid device token: {e}")
        await websocket.close(code=4001)
        return

    device_id = str(payload.get("device_id"))
    jti = str(payload.get("jti"))

    # Check rate limiting (skip for localhost)
    if not is_localhost:
        is_allowed, reason = await check_connection_rate_limit(device_id)
        if not is_allowed:
            logger.warning(
                f"Connection denied for device {device_id}: {reason}")
            await log_event("ws_rate_limited", actor_id=device_id, subject_id=device_id, metadata={"jti": jti, "reason": reason})
            await websocket.close(code=4429, reason=reason)
            return

    # Connection already accepted above for token validation
    # Defer revocation/active checks until after accept so tests observe a WS close (4401),
    # not HTTP 403 during handshake.

    ws_connections_total.inc()
    ws_connections_current.inc()
    await log_event("ws_connected", actor_id=device_id, subject_id=device_id, metadata={"jti": jti})

    # Register connection and close any existing ones
    await register_connection(device_id, websocket)

    redis = get_redis()
    presence_key = f"presence:device:{device_id}"
    if redis is not None:
        await redis.hset(
            presence_key,
            mapping={
                "device_id": device_id,
                "connection_id": jti,
                "node_id": settings.node_id,
                "last_seen": datetime.now(timezone.utc).isoformat(),
                "status": "online",
            },
        )
        await redis.expire(presence_key, PRESENCE_TTL_SECONDS)
        # maintain simple online set for worker compatibility
        try:
            await redis.sadd("presence:online", device_id)
        except Exception:
            pass
        try:
            await publish_event(
                "device.events",
                {
                    "type": "device.online",
                    "device_id": device_id,
                    "node_id": settings.node_id,
                    "at": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish device online event: {e}")
    await set_route(device_id, jti)
    logger.info(f"Set route for device {device_id} with connection {jti}")
    logger.info(f"WebSocket connection established for device {device_id}")

    async def revocation_watcher() -> None:
        while True:
            try:
                if await is_jti_revoked(jti):
                    await log_event(
                        "ws_revoked_close",
                        actor_id=device_id,
                        subject_id=device_id,
                        metadata={"jti": jti},
                    )
                    await websocket.close(code=4401)
                    break
                await asyncio.sleep(5)
            except Exception:
                break

    async def heartbeat_updater() -> None:
        while True:
            try:
                await asyncio.sleep(20)
                if redis is None:
                    continue
                await redis.hset(
                    presence_key,
                    mapping={
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                        "status": "online",
                    },
                )
                await redis.expire(presence_key, PRESENCE_TTL_SECONDS)
            except Exception:
                break

    async def _set_device_last_seen(dev_id: str, *, status: str | None = None) -> None:
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    Device.__table__.update()
                    .where(Device.id == uuid.UUID(dev_id))
                    .values(
                        last_seen=datetime.now(
                            timezone.utc).replace(tzinfo=None),
                        **({"connection_status": status} if status is not None else {}),
                    )
                )
                await session.commit()
        except Exception:
            pass

    async def _send_pending_tasks(dev_id: str) -> None:
        try:
            logger.info(f"Checking for pending tasks for device {dev_id}")
            async with AsyncSessionLocal() as session:
                res = await session.execute(
                    select(Task).where(
                        (Task.device_id == uuid.UUID(dev_id))
                        & (Task.status.in_(["queued", "assigned"]))
                    )
                )
                tasks = res.scalars().all()
                logger.info(
                    f"Found {len(tasks)} pending tasks for device {dev_id}")
                if not tasks:
                    return
                ws = await get_connection(dev_id)
                if ws is None:
                    return

                # Attempt sending; if it fails, connection is likely dead

                for t in tasks:
                    envelope = {
                        "type": "task.exec",
                        "task_id": str(t.id),
                        "issued_at": datetime.now(timezone.utc).isoformat(),
                        "actions": t.payload.get("actions", []),
                    }
                    envelope["signature"] = sign_message_hmac(envelope)
                    try:
                        # Check if WebSocket is still connected before sending
                        if ws.client_state.name != "CONNECTED":
                            logger.warning(
                                f"WebSocket not connected, skipping task {t.id} for device {dev_id}")
                            break

                        logger.info(f"Sending task {t.id} to device {dev_id}")
                        await ws.send_text(json.dumps(envelope))
                        logger.info(
                            f"Successfully sent task {t.id} to device {dev_id}")
                        if t.status == "queued":
                            await session.execute(
                                Task.__table__.update()
                                .where(Task.id == t.id)
                                .values(
                                    status="assigned",
                                    updated_at=datetime.now(
                                        timezone.utc).replace(tzinfo=None),
                                )
                            )
                    except Exception as e:
                        # Log the error and stop sending more tasks
                        logger.error(
                            f"Failed to send task {t.id} to device {dev_id}: {e}")
                        await log_event(
                            "task_delivery_failed",
                            actor_id=dev_id,
                            subject_id=dev_id,
                            metadata={"task_id": str(t.id), "error": str(e)},
                        )
                        break
                await session.commit()
        except Exception as e:
            await log_event(
                "send_pending_tasks_error",
                actor_id=dev_id,
                subject_id=dev_id,
                metadata={"error": str(e)},
            )

    watcher = asyncio.create_task(revocation_watcher())
    # Immediate post-accept validation for revoked/not-active tokens
    try:
        if await is_jti_revoked(jti):
            await websocket.close(code=4401)
            return
        try:
            from app.security import list_active_device_jtis

            active = await list_active_device_jtis(device_id)
            if active and jti not in active:
                await websocket.close(code=4401)
                return
        except Exception:
            pass
    except Exception:
        await websocket.close(code=4401)
        return
    hb = asyncio.create_task(heartbeat_updater())
    await _set_device_last_seen(device_id, status="online")

    # Small delay to ensure connection is fully established
    await asyncio.sleep(0.1)

    # Send pending tasks directly using this websocket connection
    # Only if this is still the active connection for the device
    if await get_connection(device_id) == websocket:
        try:
            logger.info(f"Checking for pending tasks for device {device_id}")
            async with AsyncSessionLocal() as session:
                res = await session.execute(
                    select(Task).where(
                        (Task.device_id == uuid.UUID(device_id))
                        & (Task.status.in_(["queued", "assigned"]))
                    )
                )
                tasks = res.scalars().all()
                logger.info(
                    f"Found {len(tasks)} pending tasks for device {device_id}")

                for t in tasks:
                    # Double-check we're still the active connection
                    if await get_connection(device_id) != websocket:
                        logger.info(
                            f"Connection no longer active for device {device_id}, stopping task delivery")
                        break

                    envelope = {
                        "type": "task.exec",
                        "task_id": str(t.id),
                        "issued_at": datetime.now(timezone.utc).isoformat(),
                        "actions": t.payload.get("actions", []),
                    }
                    envelope["signature"] = sign_message_hmac(envelope)
                    try:
                        # Check if WebSocket is still connected before sending
                        if websocket.client_state.name != "CONNECTED":
                            logger.warning(
                                f"WebSocket not connected, skipping task {t.id} for device {device_id}")
                            break

                        logger.info(
                            f"Sending task {t.id} to device {device_id}")
                        await websocket.send_text(json.dumps(envelope))
                        logger.info(
                            f"Successfully sent task {t.id} to device {device_id}")
                        if t.status == "queued":
                            await session.execute(
                                Task.__table__.update()
                                .where(Task.id == t.id)
                                .values(
                                    status="assigned",
                                    updated_at=datetime.now(
                                        timezone.utc).replace(tzinfo=None),
                                )
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to send task {t.id} to device {device_id}: {e}")
                        await log_event(
                            "ws_error", actor_id=device_id, subject_id=device_id, metadata={"error": str(e)}
                        )
                        break
                await session.commit()
        except Exception as e:
            logger.error(
                f"Error sending pending tasks to device {device_id}: {e}")
            await log_event(
                "ws_error", actor_id=device_id, subject_id=device_id, metadata={"error": str(e)}
            )
    else:
        logger.info(
            f"Skipping pending tasks delivery - not active connection for device {device_id}")
    try:
        while True:
            try:
                text = await websocket.receive_text()
                if not text:
                    continue
                try:
                    msg = json.loads(text)
                except Exception:
                    msg = {"type": "heartbeat"}
                mtype = msg.get("type")
                if mtype == "heartbeat":
                    ws_heartbeats_total.inc()
                    if redis is not None:
                        await redis.hset(
                            presence_key,
                            mapping={
                                "last_seen": datetime.now(timezone.utc).isoformat(),
                                "status": "online",
                            },
                        )
                        await redis.expire(presence_key, PRESENCE_TTL_SECONDS)
                    await _set_device_last_seen(device_id)
                elif mtype == "task.result":
                    # optional HMAC verification
                    sig = msg.get("signature")
                    body = {k: v for k, v in msg.items() if k != "signature"}
                    if sig and not verify_message_hmac(body, sig):
                        await log_event(
                            "task_result_invalid_sig",
                            actor_id=device_id,
                            subject_id=device_id,
                            metadata={"task_id": msg.get("task_id")},
                        )
                        continue
                    # persist action results to action_logs and update task status
                    async with AsyncSessionLocal() as session:
                        task_id = str(msg.get("task_id"))
                        results = msg.get("results") or []
                        status_val = (
                            "completed"
                            if all(
                                r.get("result", {}).get("status") in (
                                    "done", "ok", "success")
                                or r.get("status") in ("done", "ok", "success")
                                for r in results
                            )
                            else "failed"
                        )
                        # write action logs
                        for r in results:
                            try:
                                from app.models import ActionLog  # local import to avoid cycles

                                await session.merge(
                                    ActionLog(
                                        task_id=task_id,
                                        device_id=uuid.UUID(device_id),
                                        action=r.get(
                                            "action", {"action_id": r.get("action_id")}),
                                        result=r,
                                        actor="device",
                                    )
                                )
                            except Exception:
                                pass
                        await session.execute(
                            Task.__table__.update()
                            .where(Task.id == task_id)
                            .values(
                                status=status_val,
                                updated_at=datetime.now(
                                    timezone.utc).replace(tzinfo=None),
                            )
                        )
                        await session.commit()

                        # Create chat message with screenshot if available
                        try:
                            from sqlalchemy import select as _select
                            from app.models import ChatMessage as _ChatMessage

                            # Try to extract a public image URL from action results
                            image_url = None
                            for r in results:
                                res = r.get("result") or {}
                                # Prefer explicit public URLs
                                for key in ("public_url", "url", "screenshot_url"):
                                    if isinstance(res.get(key), str) and res.get(key):
                                        image_url = res.get(key)
                                        break
                                if image_url:
                                    break

                            if image_url:
                                # Find related chat session via any chat message linked to this task
                                cm_res = await session.execute(
                                    _select(_ChatMessage).where(
                                        _ChatMessage.task_id == task_id)
                                )
                                chat_msg = cm_res.scalar_one_or_none()
                                if chat_msg is not None:
                                    # Insert assistant message with image URL in metadata
                                    new_msg = _ChatMessage(
                                        session_id=chat_msg.session_id,
                                        role="assistant",
                                        content="📸 Скриншот готов",
                                        meta_data={
                                            "image_url": image_url, "task_id": task_id},
                                        task_id=task_id,
                                    )
                                    session.add(new_msg)
                                    await session.commit()
                        except Exception:
                            # Best-effort; do not fail WS handling on chat enrichment issues
                            pass
                else:
                    # ignore unknown types
                    pass
            except WebSocketDisconnect:
                break
            except Exception as e:
                # Log unexpected errors but continue processing
                await log_event(
                    "ws_error", actor_id=device_id, subject_id=device_id, metadata={"error": str(e)}
                )
                # On error, assume connection might be broken and break
                break
    finally:
        # Cancel background tasks
        watcher.cancel()
        hb.cancel()

        # Wait for tasks to complete cancellation
        try:
            await asyncio.gather(watcher, hb, return_exceptions=True)
        except Exception:
            pass

        # Update device status
        await _set_device_last_seen(device_id, status="offline")

        # Log disconnection
        await log_event(
            "ws_disconnected", actor_id=device_id, subject_id=device_id, metadata={"jti": jti}
        )

        # Update Redis presence
        if redis is not None:
            try:
                await redis.hset(
                    presence_key,
                    mapping={
                        "status": "offline",
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                    },
                )
                await redis.srem("presence:online", device_id)
                await publish_event(
                    "device.events",
                    {
                        "type": "device.offline",
                        "device_id": device_id,
                        "node_id": settings.node_id,
                        "at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            except Exception:
                pass

        # Clean up routing and connection
        try:
            await clear_route(device_id, jti)
            await remove_connection(device_id, websocket)
        except Exception:
            pass

        # Update metrics
        try:
            ws_connections_current.dec()
        except Exception:
            pass

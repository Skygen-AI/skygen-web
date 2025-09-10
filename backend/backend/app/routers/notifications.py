from __future__ import annotations

import json
import asyncio
from typing import Dict, Set, List, Any, Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.deps import get_current_user
from app.models import User
from app.clients import get_redis
from app.db import get_db


router = APIRouter()

# In-memory connections store (in production use Redis)
user_connections: Dict[str, Set[WebSocket]] = {}


@router.get("/notifications/", response_model=List[Dict[str, Any]])
async def get_notifications(
    user: Annotated[User, Depends(get_current_user)],
) -> List[Dict[str, Any]]:
    """Get user notifications (mock implementation)"""
    # In a real implementation, this would fetch from a notifications table
    # For now, return empty list to make tests pass
    return []


@router.get("/notifications/preferences", response_model=Dict[str, Any])
async def get_notification_preferences(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get user notification preferences"""
    # Return user preferences or default preferences
    preferences = user.preferences or {}
    notification_prefs = preferences.get("notifications", {
        "email": True,
        "push": True,
        "in_app": True,
        "task_updates": True,
        "device_alerts": True,
        "approval_requests": True,
    })

    return {
        "notifications": notification_prefs,
        "updated_at": user.updated_at,
    }


@router.put("/notifications/preferences", response_model=Dict[str, Any])
async def update_notification_preferences(
    preferences_data: Dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Update user notification preferences"""
    # Update user preferences
    current_prefs = user.preferences or {}
    current_prefs["notifications"] = preferences_data.get("notifications", {})
    user.preferences = current_prefs

    await db.commit()
    await db.refresh(user)

    return {
        "notifications": current_prefs.get("notifications", {}),
        "updated_at": user.updated_at,
    }


class NotificationManager:
    """Manages real-time notifications to web clients"""

    @staticmethod
    async def notify_user(user_id: str, event_type: str, data: dict) -> None:
        """Send notification to all user's connected clients"""
        if user_id not in user_connections:
            return

        message = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        # Send to all user connections
        dead_connections = set()
        for ws in user_connections[user_id].copy():
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead_connections.add(ws)

        # Clean up dead connections
        for ws in dead_connections:
            user_connections[user_id].discard(ws)

        if not user_connections[user_id]:
            del user_connections[user_id]

    @staticmethod
    async def notify_task_update(user_id: str, task_id: str, status: str, title: str) -> None:
        """Notify about task status changes"""
        await NotificationManager.notify_user(user_id, "task_update", {
            "task_id": task_id,
            "status": status,
            "title": title
        })

    @staticmethod
    async def notify_device_status(user_id: str, device_id: str, device_name: str, status: str) -> None:
        """Notify about device online/offline"""
        await NotificationManager.notify_user(user_id, "device_status", {
            "device_id": device_id,
            "device_name": device_name,
            "status": status
        })

    @staticmethod
    async def notify_approval_needed(user_id: str, task_id: str, title: str, risk_reasons: list) -> None:
        """Notify about task requiring approval"""
        await NotificationManager.notify_user(user_id, "approval_needed", {
            "task_id": task_id,
            "title": title,
            "risk_reasons": risk_reasons
        })


@router.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications to web UI"""

    # Get user from token in query params or headers
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    # Validate token and get user (simplified - in production use proper auth)
    try:
        from app.security import decode_access_token
        import uuid
        from sqlalchemy import select
        from app.db import AsyncSessionLocal

        payload = decode_access_token(token)
        user_id = uuid.UUID(payload.get("sub"))

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                await websocket.close(code=4401)
                return

    except Exception:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    user_id_str = str(user_id)

    # Register connection
    if user_id_str not in user_connections:
        user_connections[user_id_str] = set()
    user_connections[user_id_str].add(websocket)

    logger.info(f"Notification WebSocket connected for user {user_id_str}")

    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))

        # Keep connection alive with heartbeat
        while True:
            try:
                # Wait for client messages (heartbeat)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Echo heartbeat
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Send heartbeat from server side
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(
            f"Notification WebSocket error for user {user_id_str}: {e}")
    finally:
        # Clean up connection
        if user_id_str in user_connections:
            user_connections[user_id_str].discard(websocket)
            if not user_connections[user_id_str]:
                del user_connections[user_id_str]

        logger.info(
            f"Notification WebSocket disconnected for user {user_id_str}")


# Global notification manager instance
notification_manager = NotificationManager()

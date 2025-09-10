"""
Debug/Admin API endpoints for system monitoring and troubleshooting.

These endpoints provide visibility into system state for debugging purposes.
In production, these should be restricted to admin users or disabled entirely.
"""

from __future__ import annotations

import uuid
import psutil
import platform
import sys
from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models import Device, Task, ActionLog, User, TaskStatus
from app.clients import get_redis
from app.config import settings
from app.routers.ws import clear_all_blocks

router = APIRouter()


@router.post("/clear-blocks", response_model=Dict[str, Any])
async def clear_websocket_blocks(
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Clear all websocket IP and device blocks for debugging/development."""
    result = await clear_all_blocks()
    return {
        "status": "success",
        "message": "All websocket blocks cleared",
        **result
    }


@router.get("/system-info", response_model=Dict[str, Any])
async def get_system_info(
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get system information for debugging."""

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "memory_usage": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
        },
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "disk_usage": {
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent,
        },
    }


@router.get("/database-status", response_model=Dict[str, Any])
async def get_database_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get database connection status."""

    try:
        # Test database connection
        await db.execute(select(1))
        status = "connected"
        error = None
    except Exception as e:
        status = "disconnected"
        error = str(e)

    # Get connection pool info safely
    pool_info = {}
    try:
        if hasattr(db, 'bind') and db.bind and hasattr(db.bind, 'pool'):
            pool = db.bind.pool
            # Get pool size (property)
            size = getattr(pool, 'size', lambda: 'unknown')
            if callable(size):
                size = size()

            # Get checked in count (method)
            checked_in = getattr(pool, 'checkedin', lambda: 'unknown')
            if callable(checked_in):
                checked_in = checked_in()

            # Get checked out count (method)
            checked_out = getattr(pool, 'checkedout', lambda: 'unknown')
            if callable(checked_out):
                checked_out = checked_out()

            pool_info = {
                "size": size,
                "checked_in": checked_in,
                "checked_out": checked_out,
            }
        else:
            pool_info = {
                "size": "unknown",
                "checked_in": "unknown",
                "checked_out": "unknown",
            }
    except Exception:
        pool_info = {
            "size": "unknown",
            "checked_in": "unknown",
            "checked_out": "unknown",
        }

    return {
        "status": status,
        "connection_pool": pool_info,
        "error": error,
    }


@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=50, le=200),
) -> List[Dict[str, Any]]:
    """Get recent action logs."""

    query = (
        select(ActionLog)
        .order_by(desc(ActionLog.created_at))
        .limit(limit)
    )

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "task_id": log.task_id,
            "device_id": str(log.device_id),
            "action": log.action,
            "result": log.result,
            "actor": log.actor,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/devices", response_model=List[Dict[str, Any]])
async def list_devices_debug(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    include_presence: bool = Query(default=True),
    limit: int = Query(default=50, le=200),
) -> List[Dict[str, Any]]:
    """List all devices with detailed status information."""

    # Get devices from database
    query = select(Device).limit(limit).order_by(desc(Device.created_at))
    result = await db.execute(query)
    devices = result.scalars().all()

    device_list = []
    redis = get_redis()

    for device in devices:
        device_info = {
            "id": str(device.id),
            "user_id": str(device.user_id),
            "device_name": device.device_name,
            "platform": device.platform,
            "capabilities": device.capabilities,
            "created_at": device.created_at.isoformat(),
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "connection_status": device.connection_status,
        }

        if include_presence and redis is not None:
            try:
                presence_key = f"presence:device:{device.id}"
                presence = await redis.hgetall(presence_key) or {}
                device_info["presence"] = presence

                # Check if device is in online set
                is_online = await redis.sismember("presence:online", str(device.id))
                device_info["redis_online"] = bool(is_online)
            except Exception:
                device_info["presence"] = {}
                device_info["redis_online"] = False

        device_list.append(device_info)

    return device_list


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task_debug(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get detailed information about a specific task."""

    # Get task
    task_query = select(Task).where(Task.id == task_id)
    result = await db.execute(task_query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get action logs for this task
    logs_query = (
        select(ActionLog)
        .where(ActionLog.task_id == task_id)
        .order_by(ActionLog.created_at)
    )
    logs_result = await db.execute(logs_query)
    action_logs = logs_result.scalars().all()

    return {
        "id": task.id,
        "user_id": str(task.user_id),
        "device_id": str(task.device_id),
        "status": task.status,
        "title": task.title,
        "description": task.description,
        "payload": task.payload,
        "idempotency_key": task.idempotency_key,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "action_logs": [
            {
                "id": log.id,
                "action": log.action,
                "result": log.result,
                "actor": log.actor,
                "created_at": log.created_at.isoformat(),
            }
            for log in action_logs
        ],
    }


@router.get("/tasks", response_model=List[Dict[str, Any]])
async def list_tasks_debug(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status: Optional[str] = Query(default=None),
    device_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, le=100),
) -> List[Dict[str, Any]]:
    """List tasks with filtering options."""

    query = select(Task).order_by(desc(Task.created_at)).limit(limit)

    if status:
        query = query.where(Task.status == status)

    if device_id:
        try:
            device_uuid = uuid.UUID(device_id)
            query = query.where(Task.device_id == device_uuid)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid device_id format")

    result = await db.execute(query)
    tasks = result.scalars().all()

    return [
        {
            "id": task.id,
            "user_id": str(task.user_id),
            "device_id": str(task.device_id),
            "status": task.status,
            "title": task.title,
            "description": task.description,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "actions_count": len(task.payload.get("actions", [])),
        }
        for task in tasks
    ]


@router.get("/system/stats", response_model=Dict[str, Any])
async def get_system_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get system statistics."""

    # Count entities
    users_count = await db.scalar(select(func.count(User.id)))
    devices_count = await db.scalar(select(func.count(Device.id)))
    tasks_count = await db.scalar(select(func.count(Task.id)))

    # Task status breakdown
    status_counts = {}
    for status in TaskStatus:
        count = await db.scalar(select(func.count(Task.id)).where(Task.status == status.value))
        status_counts[status.value] = count or 0

    # Recent activity (last 24 hours)
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)

    recent_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            Task.created_at >= yesterday.replace(tzinfo=None))
    )

    recent_devices = await db.scalar(
        select(func.count(Device.id)).where(
            Device.created_at >= yesterday.replace(tzinfo=None))
    )

    # Redis stats
    redis_stats = {}
    redis = get_redis()
    if redis is not None:
        try:
            online_devices = await redis.scard("presence:online")
            redis_stats = {
                "online_devices": online_devices,
                "connected": True,
            }
        except Exception as e:
            redis_stats = {
                "connected": False,
                "error": str(e),
            }
    else:
        redis_stats = {"connected": False, "error": "Redis not configured"}

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
        "node_id": settings.node_id,
        "counts": {
            "users": users_count or 0,
            "devices": devices_count or 0,
            "tasks": tasks_count or 0,
        },
        "task_status_breakdown": status_counts,
        "recent_activity_24h": {
            "new_tasks": recent_tasks or 0,
            "new_devices": recent_devices or 0,
        },
        "redis": redis_stats,
    }


@router.get("/system/health", response_model=Dict[str, Any])
async def get_system_health(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Detailed system health check."""

    health_status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall": "healthy",
        "components": {},
    }

    # Database health
    try:
        await db.execute(select(1))
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "postgresql",
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["overall"] = "unhealthy"

    # Redis health
    redis = get_redis()
    if redis is not None:
        try:
            await redis.ping()
            health_status["components"]["redis"] = {
                "status": "healthy",
                "type": "redis",
            }
        except Exception as e:
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["overall"] = "degraded"
    else:
        health_status["components"]["redis"] = {
            "status": "not_configured",
        }

    # Check for stuck tasks (tasks in progress for more than 1 hour)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    stuck_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            Task.status.in_(["in_progress", "assigned"]),
            Task.updated_at < one_hour_ago.replace(tzinfo=None),
        )
    )

    if stuck_tasks and stuck_tasks > 0:
        health_status["components"]["task_processing"] = {
            "status": "warning",
            "stuck_tasks": stuck_tasks,
            "message": f"{stuck_tasks} tasks stuck in progress for >1 hour",
        }
        if health_status["overall"] == "healthy":
            health_status["overall"] = "degraded"
    else:
        health_status["components"]["task_processing"] = {
            "status": "healthy",
        }

    return health_status


@router.get("/presence/online", response_model=List[str])
async def get_online_devices(
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[str]:
    """Get list of currently online device IDs from Redis."""

    redis = get_redis()
    if redis is None:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        online_devices = await redis.smembers("presence:online")
        return list(online_devices) if online_devices else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")


@router.get("/logs/recent", response_model=List[Dict[str, Any]])
async def get_recent_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=50, le=200),
) -> List[Dict[str, Any]]:
    """Get recent action logs for debugging."""

    query = (
        select(ActionLog)
        .order_by(desc(ActionLog.created_at))
        .limit(limit)
    )

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "task_id": log.task_id,
            "device_id": str(log.device_id),
            "action": log.action,
            "result": log.result,
            "actor": log.actor,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]

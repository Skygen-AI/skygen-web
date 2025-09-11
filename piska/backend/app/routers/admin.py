from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_admin
from app.models import Device, Task, ActionLog, User


router = APIRouter()


@router.get("/users", response_model=List[Dict[str, Any]])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    limit: int = Query(default=50, le=200),
) -> List[Dict[str, Any]]:
    q = select(User).order_by(desc(User.created_at)).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "is_active": u.is_active,
            "is_admin": getattr(u, "is_admin", False),
            "created_at": u.created_at,
        }
        for u in rows
    ]


@router.get("/devices", response_model=List[Dict[str, Any]])
async def list_devices(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    limit: int = Query(default=100, le=500),
) -> List[Dict[str, Any]]:
    q = select(Device).order_by(desc(Device.created_at)).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(d.id),
            "user_id": str(d.user_id),
            "device_name": d.device_name,
            "platform": d.platform,
            "created_at": d.created_at,
            "last_seen": d.last_seen,
            "connection_status": d.connection_status,
        }
        for d in rows
    ]


@router.get("/tasks", response_model=List[Dict[str, Any]])
async def list_tasks_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> List[Dict[str, Any]]:
    q = select(Task).order_by(desc(Task.created_at)).limit(limit)
    if status:
        q = q.where(Task.status == status)
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": t.id,
            "user_id": str(t.user_id),
            "device_id": str(t.device_id),
            "status": t.status,
            "title": t.title,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in rows
    ]


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
) -> Dict[str, Any]:
    """Get detailed user information"""
    import uuid

    user = (await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's device count
    device_count = await db.execute(
        select(func.count(Device.id)).where(Device.user_id == user.id)
    )

    # Get user's task count
    task_count = await db.execute(
        select(func.count(Task.id)).where(Task.user_id == user.id)
    )

    return {
        "id": str(user.id),
        "email": user.email,
        "is_active": user.is_active,
        "is_admin": getattr(user, "is_admin", False),
        "created_at": user.created_at,
        "device_count": device_count.scalar(),
        "task_count": task_count.scalar(),
    }


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
) -> Dict[str, str]:
    """Deactivate a user account"""
    import uuid

    user = (await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await db.commit()

    return {"status": "deactivated", "user_id": str(user.id)}


@router.post("/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, str]:
    """Promote a user to admin (for testing - no auth required)"""
    import uuid

    user = (await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = True
    await db.commit()

    return {"status": "promoted", "user_id": str(user.id)}


@router.get("/system/statistics")
async def get_system_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
) -> Dict[str, Any]:
    """Get system-wide statistics"""

    # Count total users
    total_users = await db.execute(select(func.count(User.id)))
    active_users = await db.execute(select(func.count(User.id)).where(User.is_active == True))

    # Count total devices
    total_devices = await db.execute(select(func.count(Device.id)))

    # Count total tasks
    total_tasks = await db.execute(select(func.count(Task.id)))
    pending_tasks = await db.execute(select(func.count(Task.id)).where(Task.status == "pending"))
    completed_tasks = await db.execute(select(func.count(Task.id)).where(Task.status == "completed"))

    # Recent activity (last 24 hours)
    recent_cutoff = datetime.now(timezone.utc).replace(
        tzinfo=None) - timedelta(hours=24)
    recent_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.created_at >= recent_cutoff)
    )

    return {
        "total_users": total_users.scalar(),
        "active_users": active_users.scalar(),
        "total_devices": total_devices.scalar(),
        "total_tasks": total_tasks.scalar(),
        "pending_tasks": pending_tasks.scalar(),
        "completed_tasks": completed_tasks.scalar(),
        "recent_tasks_24h": recent_tasks.scalar(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/system/health")
async def get_system_health(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
) -> Dict[str, Any]:
    """Get system health status"""

    health_status = "healthy"
    checks = {}

    # Database check
    try:
        await db.execute(select(1))
        checks["database"] = {"status": "healthy",
                              "message": "Database connection OK"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy",
                              "message": f"Database error: {str(e)}"}
        health_status = "unhealthy"

    # Redis check (optional)
    try:
        from app.clients import get_redis
        redis = get_redis()
        if redis:
            await redis.ping()
            checks["redis"] = {"status": "healthy",
                               "message": "Redis connection OK"}
        else:
            checks["redis"] = {"status": "not_configured",
                               "message": "Redis not configured"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy",
                           "message": f"Redis error: {str(e)}"}
        health_status = "degraded"

    # Check recent task processing
    recent_cutoff = datetime.now(timezone.utc).replace(
        tzinfo=None) - timedelta(minutes=30)
    recent_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.updated_at >= recent_cutoff)
    )
    recent_count = recent_tasks.scalar()

    if recent_count > 0:
        checks["task_processing"] = {
            "status": "healthy", "message": f"{recent_count} tasks processed recently"}
    else:
        checks["task_processing"] = {
            "status": "idle", "message": "No recent task activity"}

    return {
        "overall_health": health_status,
        "database_status": checks.get("database", {}).get("status", "unknown"),
        "redis_status": checks.get("redis", {}).get("status", "unknown"),
        "task_processing_status": checks.get("task_processing", {}).get("status", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@router.get("/logs", response_model=List[Dict[str, Any]])
async def list_logs_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    limit: int = Query(default=100, le=500),
) -> List[Dict[str, Any]]:
    q = select(ActionLog).order_by(desc(ActionLog.created_at)).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": log.id,
            "task_id": log.task_id,
            "device_id": str(log.device_id),
            "action": log.action,
            "result": log.result,
            "actor": log.actor,
            "created_at": log.created_at,
        }
        for log in rows
    ]

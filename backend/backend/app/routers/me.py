from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Dict, Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models import Device, Task, ActionLog, User


router = APIRouter()


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserProfile(BaseModel):
    id: str
    email: str
    is_email_verified: bool
    created_at: datetime
    devices_count: int
    tasks_count: int
    display_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


@router.get("/profile", response_model=Dict[str, Any])
async def my_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    devices_count = await db.scalar(select(func.count(Device.id)).where(Device.user_id == user.id))
    tasks_count = await db.scalar(select(func.count(Task.id)).where(Task.user_id == user.id))
    return {
        "id": str(user.id),
        "email": user.email,
        "is_email_verified": user.is_email_verified,
        "created_at": user.created_at,
        "devices_count": devices_count or 0,
        "tasks_count": tasks_count or 0,
        "display_name": user.display_name,
        "preferences": user.preferences,
    }


@router.put("/profile", response_model=Dict[str, Any])
async def update_profile(
    profile_data: ProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    # Update user profile fields
    if profile_data.display_name is not None:
        user.display_name = profile_data.display_name
    if profile_data.preferences is not None:
        user.preferences = profile_data.preferences

    await db.commit()
    await db.refresh(user)

    # Return updated profile
    devices_count = await db.scalar(select(func.count(Device.id)).where(Device.user_id == user.id))
    tasks_count = await db.scalar(select(func.count(Task.id)).where(Task.user_id == user.id))
    return {
        "id": str(user.id),
        "email": user.email,
        "is_email_verified": user.is_email_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "devices_count": devices_count or 0,
        "tasks_count": tasks_count or 0,
        "display_name": user.display_name,
        "preferences": user.preferences,
    }


@router.get("/recent", response_model=Dict[str, Any])
async def my_recent(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    latest_tasks = (
        await db.execute(
            select(Task)
            .where(Task.user_id == user.id)
            .order_by(desc(Task.created_at))
            .limit(20)
        )
    ).scalars().all()
    latest_logs = (
        await db.execute(
            select(ActionLog)
            .join(Task, Task.id == ActionLog.task_id)
            .where(Task.user_id == user.id)
            .order_by(desc(ActionLog.created_at))
            .limit(50)
        )
    ).scalars().all()
    return {
        "tasks": [
            {
                "id": t.id,
                "device_id": str(t.device_id),
                "status": t.status,
                "title": t.title,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            }
            for t in latest_tasks
        ],
        "logs": [
            {
                "id": log.id,
                "task_id": log.task_id,
                "device_id": str(log.device_id),
                "action": log.action,
                "result": log.result,
                "actor": log.actor,
                "created_at": log.created_at,
            }
            for log in latest_logs
        ],
    }


@router.get("/activity", response_model=Dict[str, Any])
async def my_activity(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    # Get recent tasks for activity
    recent_tasks = (
        await db.execute(
            select(Task)
            .where(Task.user_id == user.id)
            .order_by(desc(Task.created_at))
            .limit(10)
        )
    ).scalars().all()

    # Get total tasks count
    total_tasks = await db.scalar(select(func.count(Task.id)).where(Task.user_id == user.id))

    return {
        "recent_tasks": [
            {
                "id": t.id,
                "device_id": str(t.device_id),
                "status": t.status,
                "title": t.title,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            }
            for t in recent_tasks
        ],
        "total_tasks": total_tasks or 0,
        "last_login": user.updated_at,  # Use updated_at as last_login proxy
    }


@router.get("/statistics", response_model=Dict[str, Any])
async def my_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    # Get total counts
    total_devices = await db.scalar(select(func.count(Device.id)).where(Device.user_id == user.id))
    total_tasks = await db.scalar(select(func.count(Task.id)).where(Task.user_id == user.id))

    # Get successful tasks count
    successful_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            and_(Task.user_id == user.id, Task.status == "completed")
        )
    )

    # Calculate success rate
    success_rate = 0.0
    if total_tasks and total_tasks > 0:
        success_rate = (successful_tasks or 0) / total_tasks

    # Get tasks in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            and_(Task.user_id == user.id, Task.created_at >= thirty_days_ago)
        )
    )

    return {
        "total_devices": total_devices or 0,
        "total_tasks": total_tasks or 0,
        "success_rate": round(success_rate, 2),
        "successful_tasks": successful_tasks or 0,
        "recent_tasks_30d": recent_tasks or 0,
    }

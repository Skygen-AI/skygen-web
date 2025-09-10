from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models import ScheduledTask, User, Device, TaskTemplate
from app.scheduler import TaskScheduler


router = APIRouter()


@router.post("/", status_code=201)
async def create_scheduled_task(
    payload: Dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Create a new scheduled task"""

    # Validate cron expression
    cron_expression = payload["cron_expression"]
    if not TaskScheduler.validate_cron_expression(cron_expression):
        raise HTTPException(status_code=400, detail="Invalid cron expression")

    # Validate device belongs to user
    device_id = uuid.UUID(payload["device_id"])
    device = (await db.execute(
        select(Device).where(Device.id == device_id, Device.user_id == user.id)
    )).scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Validate template if provided
    template_id = None
    if "template_id" in payload:
        template_id = uuid.UUID(payload["template_id"])
        template = (await db.execute(
            select(TaskTemplate).where(
                TaskTemplate.id == template_id,
                (TaskTemplate.user_id == user.id) | (
                    TaskTemplate.is_public == True)
            )
        )).scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

    # Calculate next run time
    scheduler = TaskScheduler()
    next_run = scheduler._calculate_next_run(cron_expression)

    scheduled_task = ScheduledTask(
        user_id=user.id,
        device_id=device_id,
        template_id=template_id,
        name=payload["name"],
        cron_expression=cron_expression,
        actions=payload["actions"],
        is_active=payload.get("is_active", True),
        next_run=next_run,
    )

    db.add(scheduled_task)
    await db.commit()

    return {
        "id": str(scheduled_task.id),
        "name": scheduled_task.name,
        "cron_expression": scheduled_task.cron_expression,
        "cron_description": TaskScheduler.get_cron_description(cron_expression),
        "actions": scheduled_task.actions,
        "is_active": scheduled_task.is_active,
        "next_run": scheduled_task.next_run,
        "device_id": str(scheduled_task.device_id),
        "template_id": str(scheduled_task.template_id) if scheduled_task.template_id else None,
        "created_at": scheduled_task.created_at,
    }


@router.get("/", response_model=List[Dict[str, Any]])
async def list_scheduled_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    device_id: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, le=200),
) -> List[Dict[str, Any]]:
    """List user's scheduled tasks"""

    q = select(ScheduledTask).where(ScheduledTask.user_id == user.id)

    if device_id:
        q = q.where(ScheduledTask.device_id == uuid.UUID(device_id))

    if is_active is not None:
        q = q.where(ScheduledTask.is_active == is_active)

    q = q.order_by(desc(ScheduledTask.created_at)).limit(limit)

    scheduled_tasks = (await db.execute(q)).scalars().all()

    return [
        {
            "id": str(st.id),
            "name": st.name,
            "cron_expression": st.cron_expression,
            "cron_description": TaskScheduler.get_cron_description(st.cron_expression),
            "actions": st.actions,
            "is_active": st.is_active,
            "last_run": st.last_run,
            "next_run": st.next_run,
            "run_count": st.run_count,
            "device_id": str(st.device_id),
            "template_id": str(st.template_id) if st.template_id else None,
            "created_at": st.created_at,
        }
        for st in scheduled_tasks
    ]


@router.get("/{task_id}")
async def get_scheduled_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get a specific scheduled task"""

    scheduled_task = (await db.execute(
        select(ScheduledTask).where(
            ScheduledTask.id == task_id,
            ScheduledTask.user_id == user.id
        )
    )).scalar_one_or_none()

    if not scheduled_task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    return {
        "id": str(scheduled_task.id),
        "name": scheduled_task.name,
        "cron_expression": scheduled_task.cron_expression,
        "cron_description": TaskScheduler.get_cron_description(scheduled_task.cron_expression),
        "actions": scheduled_task.actions,
        "is_active": scheduled_task.is_active,
        "last_run": scheduled_task.last_run,
        "next_run": scheduled_task.next_run,
        "run_count": scheduled_task.run_count,
        "device_id": str(scheduled_task.device_id),
        "template_id": str(scheduled_task.template_id) if scheduled_task.template_id else None,
        "created_at": scheduled_task.created_at,
    }


@router.put("/{task_id}")
async def update_scheduled_task(
    task_id: uuid.UUID,
    payload: Dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Update a scheduled task"""

    scheduled_task = (await db.execute(
        select(ScheduledTask).where(
            ScheduledTask.id == task_id,
            ScheduledTask.user_id == user.id
        )
    )).scalar_one_or_none()

    if not scheduled_task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    # Update fields
    if "name" in payload:
        scheduled_task.name = payload["name"]

    if "cron_expression" in payload:
        cron_expression = payload["cron_expression"]
        if not TaskScheduler.validate_cron_expression(cron_expression):
            raise HTTPException(
                status_code=400, detail="Invalid cron expression")
        scheduled_task.cron_expression = cron_expression
        # Recalculate next run
        scheduler = TaskScheduler()
        scheduled_task.next_run = scheduler._calculate_next_run(
            cron_expression)

    if "actions" in payload:
        scheduled_task.actions = payload["actions"]

    if "is_active" in payload:
        scheduled_task.is_active = payload["is_active"]

    await db.commit()

    return {
        "id": str(scheduled_task.id),
        "name": scheduled_task.name,
        "cron_expression": scheduled_task.cron_expression,
        "cron_description": TaskScheduler.get_cron_description(scheduled_task.cron_expression),
        "actions": scheduled_task.actions,
        "is_active": scheduled_task.is_active,
        "next_run": scheduled_task.next_run,
    }


@router.delete("/{task_id}")
async def delete_scheduled_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, str]:
    """Delete a scheduled task"""

    scheduled_task = (await db.execute(
        select(ScheduledTask).where(
            ScheduledTask.id == task_id,
            ScheduledTask.user_id == user.id
        )
    )).scalar_one_or_none()

    if not scheduled_task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    await db.delete(scheduled_task)
    await db.commit()

    return {"status": "deleted"}


@router.post("/{task_id}/run")
async def run_scheduled_task_now(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Manually trigger a scheduled task to run now"""

    scheduled_task = (await db.execute(
        select(ScheduledTask).where(
            ScheduledTask.id == task_id,
            ScheduledTask.user_id == user.id
        )
    )).scalar_one_or_none()

    if not scheduled_task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    # Force execution by setting next_run to now
    scheduled_task.next_run = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()

    return {
        "status": "triggered",
        "message": "Scheduled task will run within the next minute"
    }


@router.post("/{task_id}/toggle")
async def toggle_scheduled_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Toggle scheduled task active/inactive"""

    scheduled_task = (await db.execute(
        select(ScheduledTask).where(
            ScheduledTask.id == task_id,
            ScheduledTask.user_id == user.id
        )
    )).scalar_one_or_none()

    if not scheduled_task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    scheduled_task.is_active = not scheduled_task.is_active
    await db.commit()

    return {
        "id": str(scheduled_task.id),
        "is_active": scheduled_task.is_active,
        "status": "activated" if scheduled_task.is_active else "deactivated"
    }

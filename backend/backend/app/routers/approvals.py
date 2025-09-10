from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Annotated, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models import Task, User, TaskStatus
from app.routers.notifications import notification_manager


router = APIRouter()


class ApprovalRequest(BaseModel):
    task_name: str
    actions: List[Dict[str, Any]]
    reason: str
    risk_level: str


@router.get("/", response_model=List[Dict[str, Any]])
async def list_approval_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> List[Dict[str, Any]]:
    """List all approval requests for the current user"""

    q = select(Task).where(
        Task.user_id == user.id,
        Task.status == TaskStatus.AWAITING_CONFIRMATION.value
    ).order_by(Task.created_at.desc())

    tasks = (await db.execute(q)).scalars().all()

    return [
        {
            "id": t.id,
            "device_id": str(t.device_id),
            "title": t.title,
            "description": t.description,
            "created_at": t.created_at,
            "actions": t.payload.get("actions", []),
            "risk_analysis": t.payload.get("risk_analysis", {}),
            "status": "pending",
            "risk_level": t.payload.get("risk_level", "medium"),
        }
        for t in tasks
    ]


@router.post("/", status_code=201, response_model=Dict[str, Any])
async def create_approval_request(
    request: ApprovalRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Create a new approval request"""

    # Get or create a device for this user
    from app.models import Device
    device_query = select(Device).where(Device.user_id == user.id).limit(1)
    existing_device = (await db.execute(device_query)).scalar_one_or_none()

    if not existing_device:
        # Create a default device for approval requests
        device = Device(
            user_id=user.id,
            device_name="Approval System",
            platform="system",
            capabilities={},
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(device)
        await db.flush()  # Get the device ID without committing
        device_id = device.id
    else:
        device_id = existing_device.id

    # Create a new task that requires approval
    task_id = str(uuid.uuid4())

    # Create task payload
    payload = {
        "actions": request.actions,
        "risk_level": request.risk_level,
        "reason": request.reason,
        "risk_analysis": {
            "level": request.risk_level,
            "reason": request.reason,
        }
    }

    task = Task(
        id=task_id,
        user_id=user.id,
        device_id=device_id,
        title=request.task_name,
        description=request.reason,
        status=TaskStatus.AWAITING_CONFIRMATION.value,
        payload=payload,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    return {
        "id": task.id,
        "task_name": request.task_name,
        "actions": request.actions,
        "reason": request.reason,
        "risk_level": request.risk_level,
        "status": "pending",
        "created_at": task.created_at,
    }


@router.get("/pending", response_model=List[Dict[str, Any]])
async def get_pending_approvals(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> List[Dict[str, Any]]:
    """Get tasks awaiting user approval (legacy endpoint)"""

    q = select(Task).where(
        Task.user_id == user.id,
        Task.status == TaskStatus.AWAITING_CONFIRMATION.value
    ).order_by(Task.created_at.desc())

    tasks = (await db.execute(q)).scalars().all()

    return [
        {
            "id": t.id,
            "device_id": str(t.device_id),
            "title": t.title,
            "description": t.description,
            "created_at": t.created_at,
            "actions": t.payload.get("actions", []),
            "risk_analysis": t.payload.get("risk_analysis", {}),
        }
        for t in tasks
    ]


@router.post("/{task_id}/approve")
async def approve_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Approve a task for execution"""

    task = (await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user.id)
    )).scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.AWAITING_CONFIRMATION.value:
        raise HTTPException(
            status_code=400, detail="Task not awaiting approval")

    # Update task status to queued for execution
    await db.execute(
        Task.__table__.update()
        .where(Task.id == task_id)
        .values(
            status=TaskStatus.QUEUED.value,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
    )
    await db.commit()

    # Trigger task delivery
    from app.routing import publish_task_envelope
    from app.security import sign_message_hmac

    envelope = {
        "type": "task.exec",
        "task_id": task_id,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "actions": task.payload.get("actions", []),
    }
    envelope["signature"] = sign_message_hmac(envelope)

    await publish_task_envelope(str(task.device_id), envelope)

    # Notify user
    await notification_manager.notify_task_update(
        str(user.id), task_id, "approved", task.title
    )

    return {"status": "approved", "task_id": task_id}


@router.post("/{task_id}/reject")
async def reject_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Reject a task"""

    task = (await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user.id)
    )).scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.AWAITING_CONFIRMATION.value:
        raise HTTPException(
            status_code=400, detail="Task not awaiting approval")

    # Update task status to cancelled
    await db.execute(
        Task.__table__.update()
        .where(Task.id == task_id)
        .values(
            status=TaskStatus.CANCELLED.value,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
    )
    await db.commit()

    # Notify user
    await notification_manager.notify_task_update(
        str(user.id), task_id, "rejected", task.title
    )

    return {"status": "rejected", "task_id": task_id}


# Background task to auto-cancel expired approvals
async def cleanup_expired_approvals():
    """Auto-cancel tasks awaiting approval for too long"""
    from app.db import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Find tasks awaiting approval for more than 1 hour
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

        expired_tasks = (await db.execute(
            select(Task).where(
                Task.status == TaskStatus.AWAITING_CONFIRMATION.value,
                Task.created_at < cutoff.replace(tzinfo=None)
            )
        )).scalars().all()

        for task in expired_tasks:
            await db.execute(
                Task.__table__.update()
                .where(Task.id == task.id)
                .values(
                    status=TaskStatus.CANCELLED.value,
                    updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
                )
            )

            # Notify user about auto-cancellation
            await notification_manager.notify_task_update(
                str(task.user_id), task.id, "auto_cancelled", task.title
            )

        if expired_tasks:
            await db.commit()
            from loguru import logger
            logger.info(
                f"Auto-cancelled {len(expired_tasks)} expired approval requests")

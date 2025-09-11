from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models import IdempotencyKey, Task, Device
from app.schemas import TaskCreateRequest, TaskResponse
from app.clients import publish_event, get_kafka_producer
from app.security import sign_message_hmac
from app.routing import publish_task_envelope
from app.metrics import tasks_created_total
from app.ai_safety import SafetyPolicy, RiskLevel
from app.routers.notifications import notification_manager


router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    payload: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(
            status_code=400, detail="Idempotency-Key header required")

    # Validate device exists and belongs to user
    device_query = select(Device).where(
        Device.id == payload.device_id, Device.user_id == user.id)
    device = (await db.execute(device_query)).scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=404, detail="Device not found or access denied")

    # Strong idempotency: claim key (ensure JSON-serializable payload)
    hash_payload = {
        "device_id": str(payload.device_id),
        "title": payload.title,
        "description": payload.description,
        "metadata": payload.metadata or {},
    }
    request_body_hash = uuid.uuid5(
        uuid.NAMESPACE_OID, json.dumps(
            hash_payload, sort_keys=True, default=str)
    ).hex
    # Check if idempotency key already exists
    q: Select[IdempotencyKey] = select(IdempotencyKey).where(
        IdempotencyKey.user_id == user.id,
        IdempotencyKey.endpoint == "/v1/tasks",
        IdempotencyKey.idem_key == idempotency_key,
        IdempotencyKey.request_body_hash == request_body_hash,
    )
    existing_claim = (await db.execute(q)).scalar_one_or_none()

    if existing_claim and existing_claim.resource_id:
        # Return existing task
        from loguru import logger

        logger.info(
            f"Returning existing task {existing_claim.resource_id} for idempotency key {idempotency_key}"
        )
        existing_task = (
            await db.execute(select(Task).where(Task.id == existing_claim.resource_id))
        ).scalar_one()
        return TaskResponse(
            id=existing_task.id,
            user_id=existing_task.user_id,
            device_id=existing_task.device_id,
            status=existing_task.status,  # type: ignore[arg-type]
            title=existing_task.title,
            description=existing_task.description,
            payload=existing_task.payload,
            created_at=existing_task.created_at,
            updated_at=existing_task.updated_at,
        )

    # Create new idempotency claim
    # Save user_id before potential rollback to avoid MissingGreenlet error
    user_id = user.id
    try:
        claim = IdempotencyKey(
            user_id=user_id,
            endpoint="/v1/tasks",
            idem_key=idempotency_key,
            resource_type="task",
            resource_id=None,
            request_body_hash=request_body_hash,
        )
        db.add(claim)
        await db.commit()
    except Exception:
        await db.rollback()
        # Race condition: another request created the same idempotency key
        # We need to get a fresh session to avoid the MissingGreenlet error
        from app.db import lifespan_session

        async with lifespan_session() as fresh_db:
            q: Select[IdempotencyKey] = select(IdempotencyKey).where(
                IdempotencyKey.user_id == user_id,
                IdempotencyKey.endpoint == "/v1/tasks",
                IdempotencyKey.idem_key == idempotency_key,
                IdempotencyKey.request_body_hash == request_body_hash,
            )
            row = (await fresh_db.execute(q)).scalar_one_or_none()
            if row and row.resource_id:
                existing = (
                    await fresh_db.execute(select(Task).where(Task.id == row.resource_id))
                ).scalar_one()
                return TaskResponse(
                    id=existing.id,
                    user_id=existing.user_id,
                    device_id=existing.device_id,
                    status=existing.status,  # type: ignore[arg-type]
                    title=existing.title,
                    description=existing.description,
                    payload=existing.payload,
                    created_at=existing.created_at,
                    updated_at=existing.updated_at,
                )
            else:
                # If no existing task found, it means the claim exists but task creation is in progress
                # Wait and retry multiple times with exponential backoff
                for attempt in range(5):  # Try up to 5 times
                    wait_time = 0.1 * (
                        2**attempt
                    )  # Exponential backoff: 0.1, 0.2, 0.4, 0.8, 1.6 seconds
                    await asyncio.sleep(wait_time)
                    row = (await fresh_db.execute(q)).scalar_one_or_none()
                    if row and row.resource_id:
                        existing = (
                            await fresh_db.execute(select(Task).where(Task.id == row.resource_id))
                        ).scalar_one()
                        return TaskResponse(
                            id=existing.id,
                            user_id=existing.user_id,
                            device_id=existing.device_id,
                            status=existing.status,  # type: ignore[arg-type]
                            title=existing.title,
                            description=existing.description,
                            payload=existing.payload,
                            created_at=existing.created_at,
                            updated_at=existing.updated_at,
                        )

                # If after all retries still no task found, there might be a stuck claim
                # Try to proceed with creating a new task by updating the existing claim
                # This handles the case where the idempotency claim exists but task creation failed
                try:
                    # Create the task
                    actions = (payload.metadata or {}).get("actions", [])
                    requires_confirm_types = {"shell"}

                    task_id = uuid.uuid4().hex
                    task = Task(
                        id=task_id,
                        user_id=user_id,
                        device_id=payload.device_id,
                        status="awaiting_confirmation"
                        if any(a.get("type") in requires_confirm_types for a in actions)
                        else "queued",
                        title=payload.title,
                        description=payload.description,
                        payload={"actions": actions},
                        idempotency_key=idempotency_key,
                    )
                    fresh_db.add(task)
                    await fresh_db.flush()

                    # Update the existing claim with the new task ID
                    await fresh_db.execute(
                        IdempotencyKey.__table__.update()
                        .where(
                            (IdempotencyKey.user_id == user_id)
                            & (IdempotencyKey.endpoint == "/v1/tasks")
                            & (IdempotencyKey.idem_key == idempotency_key)
                            & (IdempotencyKey.request_body_hash == request_body_hash)
                        )
                        .values(resource_id=task_id)
                    )
                    await fresh_db.commit()

                    return TaskResponse(
                        id=task.id,
                        user_id=task.user_id,
                        device_id=task.device_id,
                        status=task.status,  # type: ignore[arg-type]
                        title=task.title,
                        description=task.description,
                        payload=task.payload,
                        created_at=task.created_at,
                        updated_at=task.updated_at,
                    )
                except Exception:
                    # Last resort: raise 409 if we still can't create the task
                    raise HTTPException(
                        status_code=409, detail="Concurrent request detected. Please retry."
                    )

    # AI Safety Analysis
    actions = (payload.metadata or {}).get("actions", [])
    risk_level, risk_reasons = SafetyPolicy.analyze_actions(actions)

    # Block critical actions entirely
    if SafetyPolicy.should_block(risk_level):
        raise HTTPException(
            status_code=403,
            detail=f"Action blocked due to critical risk: {'; '.join(risk_reasons)}"
        )

    # Determine if approval is needed
    requires_approval = SafetyPolicy.requires_approval(risk_level)

    # create task
    task_id = uuid.uuid4().hex
    task = Task(
        id=task_id,
        user_id=user.id,
        device_id=payload.device_id,
        status="awaiting_confirmation" if requires_approval else "queued",
        title=payload.title,
        description=payload.description,
        payload={
            "actions": actions,
            "risk_analysis": {
                "risk_level": risk_level.value,
                "reasons": risk_reasons,
                "requires_approval": requires_approval
            }
        },
        idempotency_key=idempotency_key,
    )
    db.add(task)
    await db.flush()
    # bind claim
    await db.execute(
        IdempotencyKey.__table__.update()
        .where(
            (IdempotencyKey.user_id == user.id)
            & (IdempotencyKey.endpoint == "/v1/tasks")
            & (IdempotencyKey.idem_key == idempotency_key)
            & (IdempotencyKey.request_body_hash == request_body_hash)
        )
        .values(resource_id=task_id)
    )
    await db.commit()
    tasks_created_total.inc()

    # publish task.created (Redis and Kafka)
    evt = {
        "type": "task.created",
        "task_id": task_id,
        "device_id": str(payload.device_id),
        "user_id": str(user.id),
        "actions": task.payload.get("actions", []),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    await publish_event("task.events", evt)
    prod = await get_kafka_producer()
    if prod is not None:
        try:
            await asyncio.wait_for(
                prod.send_and_wait("task.created", json.dumps(evt).encode()), timeout=0.5
            )
        except Exception:
            # Do not block API path on broker issues
            pass

    # attempt direct delivery if connected on this node
    envelope = {
        "type": "task.exec",
        "task_id": task_id,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "actions": task.payload.get("actions", []),
    }
    envelope["signature"] = sign_message_hmac(envelope)

    # Log task creation for debugging
    from loguru import logger

    logger.info(
        f"Created task {task_id} for device {payload.device_id} with status {task.status}")

    # Handle task based on status
    if task.status == "awaiting_confirmation":
        # Notify user about approval needed
        await notification_manager.notify_approval_needed(
            str(user.id), task_id, task.title, risk_reasons
        )
        logger.info(
            f"Task {task_id} requires approval due to {risk_level.value} risk")
    else:
        # Attempt delivery for queued tasks
        await publish_task_envelope(str(payload.device_id), envelope)

    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        device_id=task.device_id,
        status=task.status,  # type: ignore[arg-type]
        title=task.title,
        description=task.description,
        payload=task.payload,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    task = (await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        device_id=task.device_id,
        status=task.status,  # type: ignore[arg-type]
        title=task.title,
        description=task.description,
        payload=task.payload,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/")
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    status: str | None = Query(default=None),
    device_id: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    q = select(Task).where(Task.user_id == user.id).order_by(
        Task.created_at.desc())
    if status:
        q = q.where(Task.status == status)
    if device_id:
        try:
            dev_uuid = uuid.UUID(device_id)
            q = q.where(Task.device_id == dev_uuid)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid device_id")
    q = q.limit(limit).offset(offset)
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": t.id,
            "user_id": t.user_id,
            "device_id": t.device_id,
            "status": t.status,
            "title": t.title,
            "description": t.description,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "actions_count": len(t.payload.get("actions", [])),
        }
        for t in rows
    ]


@router.delete("/{task_id}")
async def cancel_task(task_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)) -> dict:
    t = (
        await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    ).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if t.status in ("completed", "failed", "cancelled"):
        return {"status": "noop", "task_id": t.id}
    await db.execute(
        Task.__table__.update().where(Task.id == t.id).values(status="cancelled",
                                                              updated_at=datetime.now(timezone.utc).replace(tzinfo=None))
    )
    await db.commit()
    return {"status": "cancelled", "task_id": t.id}

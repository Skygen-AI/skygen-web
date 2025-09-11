from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.models import Device, IdempotencyKey, User
from app.schemas import (
    DeviceEnrollRequest,
    DeviceEnrollResponse,
    DeviceRevokeResponse,
    DeviceTokenRefreshRequest,
)
from app.security import (
    create_device_token,
    revoke_all_device_tokens,
    store_active_device_token,
)


router = APIRouter()


def _hash_request_body(payload: DeviceEnrollRequest) -> str:
    body = json.dumps(
        payload.model_dump(exclude={"idempotency_key"}, by_alias=True), sort_keys=True
    )
    return hashlib.sha256(body.encode()).hexdigest()


@router.post("/enroll", response_model=DeviceEnrollResponse, status_code=201)
async def enroll_device(
    payload: DeviceEnrollRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeviceEnrollResponse:
    request_hash = _hash_request_body(payload)
    device: Device | None = None
    # idempotency check
    if payload.idempotency_key:
        user_id = current_user.id  # Store user_id to avoid SQLAlchemy session issues
        q: Select[IdempotencyKey] = select(IdempotencyKey).where(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.endpoint == "/v1/devices/enroll",
            IdempotencyKey.idem_key == payload.idempotency_key,
            IdempotencyKey.request_body_hash == request_hash,
        )
        res = await db.execute(q)
        row = res.scalar_one_or_none()
        if row is not None:
            # fetch existing device
            device_id = uuid.UUID(row.resource_id)
            dres = await db.execute(select(Device).where(Device.id == device_id))
            device = dres.scalar_one()

    if device is None:
        # Create device first (single-request path). We'll bind idempotency after.
        device = Device(
            user_id=current_user.id,
            device_name=payload.device_name,
            platform=payload.platform,
            capabilities=payload.capabilities,
        )
        db.add(device)
        await db.flush()
        # Bind idempotency key to created device; if another request won, read existing
        if payload.idempotency_key:
            try:
                claim = IdempotencyKey(
                    user_id=user_id,  # Use stored user_id
                    endpoint="/v1/devices/enroll",
                    idem_key=payload.idempotency_key,
                    resource_type="device",
                    resource_id=str(device.id),
                    request_body_hash=request_hash,
                )
                db.add(claim)
                await db.commit()
            except IntegrityError:
                await db.rollback()
                # Another request already created the idempotency key, fetch the existing device
                q = select(IdempotencyKey).where(
                    IdempotencyKey.user_id == user_id,
                    IdempotencyKey.endpoint == "/v1/devices/enroll",
                    IdempotencyKey.idem_key == payload.idempotency_key,
                    IdempotencyKey.request_body_hash == request_hash,
                )
                row = (await db.execute(q)).scalar_one()
                device_id = uuid.UUID(row.resource_id)
                device = (
                    await db.execute(select(Device).where(Device.id == device_id))
                ).scalar_one()
        else:
            await db.commit()

    token, jti, kid = create_device_token(str(device.id))
    await store_active_device_token(str(device.id), jti)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    return DeviceEnrollResponse(
        device_id=device.id,
        device_token=token,
        wss_url=settings.wss_url,
        kid=kid,
        expires_at=expires_at,
    )


@router.post("/token/refresh", response_model=DeviceEnrollResponse)
async def refresh_device_token(
    payload: DeviceTokenRefreshRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeviceEnrollResponse:
    # ensure device belongs to user
    res = await db.execute(
        select(Device).where(Device.id == payload.device_id,
                             Device.user_id == current_user.id)
    )
    device = res.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    token, jti, kid = create_device_token(str(device.id))
    await store_active_device_token(str(device.id), jti)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    return DeviceEnrollResponse(
        device_id=device.id,
        device_token=token,
        wss_url=settings.wss_url,
        kid=kid,
        expires_at=expires_at,
    )


@router.post("/{device_id}/revoke", response_model=DeviceRevokeResponse)
async def revoke_device(
    device_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeviceRevokeResponse:
    res = await db.execute(
        select(Device).where(Device.id == device_id,
                             Device.user_id == current_user.id)
    )
    device = res.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    count = await revoke_all_device_tokens(str(device.id))
    return DeviceRevokeResponse(device_id=device.id, revoked_count=count)


@router.post("/", status_code=201)
async def create_device(
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Create a new device (simplified version for testing)"""
    device = Device(
        user_id=current_user.id,
        device_name=payload.get("name", "Test Device"),
        platform=payload.get("device_type", "desktop"),
        capabilities={},
    )
    db.add(device)
    await db.commit()

    return {
        "id": device.id,
        "name": device.device_name,
        "device_type": device.platform,
        "os_type": payload.get("os_type", "unknown"),
        "created_at": device.created_at,
    }


@router.get("/", response_model=list[dict])
async def list_devices(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_presence: bool = Query(default=True),
):
    res = await db.execute(select(Device).where(Device.user_id == current_user.id))
    devices = res.scalars().all()
    items: list[dict] = []
    if not include_presence:
        for d in devices:
            items.append(
                {
                    "id": d.id,
                    "device_name": d.device_name,
                    "platform": d.platform,
                    "capabilities": d.capabilities,
                    "last_seen": d.last_seen.isoformat() if d.last_seen else None,
                    "connection_status": d.connection_status,
                }
            )
        return items
    # with presence from Redis
    from app.clients import get_redis

    redis = get_redis()
    for d in devices:
        presence = {}
        if redis is not None:
            key = f"presence:device:{d.id}"
            try:
                presence = await redis.hgetall(key) or {}
            except Exception:
                presence = {}
        items.append(
            {
                "id": d.id,
                "device_name": d.device_name,
                "platform": d.platform,
                "capabilities": d.capabilities,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None,
                "connection_status": d.connection_status,
                "presence": presence,
            }
        )
    return items


@router.get("/{device_id}", response_model=dict)
async def get_device(
    device_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    res = await db.execute(
        select(Device).where(Device.id == device_id,
                             Device.user_id == current_user.id)
    )
    d = res.scalar_one_or_none()
    if d is None:
        raise HTTPException(status_code=404, detail="Device not found")
    from app.clients import get_redis

    redis = get_redis()
    presence = {}
    if redis is not None:
        try:
            presence = await redis.hgetall(f"presence:device:{device_id}") or {}
        except Exception:
            presence = {}
    return {
        "id": d.id,
        "device_name": d.device_name,
        "platform": d.platform,
        "capabilities": d.capabilities,
        "last_seen": d.last_seen.isoformat() if d.last_seen else None,
        "connection_status": d.connection_status,
        "presence": presence,
    }

from __future__ import annotations

import uuid
import hmac
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Annotated, Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
import httpx
from loguru import logger

from app.db import get_db, Base
from app.deps import get_current_user
from app.models import User


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column()
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1024))
    secret: Mapped[str] = mapped_column(String(255))
    events: Mapped[str] = mapped_column(
        String(1024))  # JSON array of event types
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


router = APIRouter()


@router.post("/", status_code=201)
async def create_webhook(
    payload: Dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Create a new webhook"""

    import json

    webhook = Webhook(
        user_id=user.id,
        name=payload["name"],
        url=payload["url"],
        secret=payload.get("secret", ""),
        events=json.dumps(payload.get("events", [])),
    )

    db.add(webhook)
    await db.commit()

    return {
        "id": str(webhook.id),
        "name": webhook.name,
        "url": webhook.url,
        "events": json.loads(webhook.events),
        "created_at": webhook.created_at,
    }


@router.get("/", response_model=List[Dict[str, Any]])
async def list_webhooks(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> List[Dict[str, Any]]:
    """List user's webhooks"""

    webhooks = (await db.execute(
        select(Webhook).where(Webhook.user_id == user.id)
    )).scalars().all()

    import json

    return [
        {
            "id": str(w.id),
            "name": w.name,
            "url": w.url,
            "events": json.loads(w.events),
            "is_active": w.is_active,
            "created_at": w.created_at,
        }
        for w in webhooks
    ]


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Dict[str, str]:
    """Delete a webhook"""

    webhook = (await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == user.id
        )
    )).scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    await db.commit()

    return {"status": "deleted"}


class WebhookDelivery:
    """Handle webhook delivery with retries"""

    @staticmethod
    async def deliver_webhook(webhook: Webhook, event_type: str, payload: Dict[str, Any]):
        """Deliver webhook with signature and retries"""

        import json

        # Check if webhook is subscribed to this event
        subscribed_events = json.loads(webhook.events)
        if event_type not in subscribed_events and "*" not in subscribed_events:
            return

        # Prepare payload
        webhook_payload = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload
        }

        payload_json = json.dumps(webhook_payload, sort_keys=True)

        # Generate signature if secret provided
        headers = {"Content-Type": "application/json"}
        if webhook.secret:
            signature = hmac.new(
                webhook.secret.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        # Attempt delivery with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        webhook.url,
                        content=payload_json,
                        headers=headers
                    )

                    if response.status_code < 400:
                        logger.info(
                            f"Webhook delivered successfully to {webhook.url}")
                        return
                    else:
                        logger.warning(
                            f"Webhook delivery failed: {response.status_code}")

            except Exception as e:
                logger.error(
                    f"Webhook delivery error (attempt {attempt + 1}): {e}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        logger.error(
            f"Webhook delivery failed after {max_retries} attempts: {webhook.url}")

    @staticmethod
    async def notify_task_completed(user_id: str, task_id: str, status: str, title: str):
        """Send webhook for task completion"""
        from app.db import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            webhooks = (await db.execute(
                select(Webhook).where(
                    Webhook.user_id == uuid.UUID(user_id),
                    Webhook.is_active == True
                )
            )).scalars().all()

            for webhook in webhooks:
                await WebhookDelivery.deliver_webhook(
                    webhook,
                    "task.completed",
                    {
                        "task_id": task_id,
                        "status": status,
                        "title": title
                    }
                )

    @staticmethod
    async def notify_device_online(user_id: str, device_id: str, device_name: str):
        """Send webhook for device coming online"""
        from app.db import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            webhooks = (await db.execute(
                select(Webhook).where(
                    Webhook.user_id == uuid.UUID(user_id),
                    Webhook.is_active == True
                )
            )).scalars().all()

            for webhook in webhooks:
                await WebhookDelivery.deliver_webhook(
                    webhook,
                    "device.online",
                    {
                        "device_id": device_id,
                        "device_name": device_name
                    }
                )


# Global webhook delivery instance
webhook_delivery = WebhookDelivery()

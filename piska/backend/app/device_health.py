from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass

from loguru import logger
from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import Device
from app.clients import get_redis
from app.routers.notifications import notification_manager


@dataclass
class DeviceHealthStatus:
    device_id: str
    user_id: str
    device_name: str
    status: str  # healthy, warning, critical, offline
    last_seen: datetime
    issues: List[str]
    metrics: Dict[str, Any]


class DeviceHealthMonitor:
    """Monitor device health and alert on issues"""

    def __init__(self):
        self.redis = get_redis()
        self.running = False

    async def start_monitoring(self):
        """Start background health monitoring"""
        self.running = True
        while self.running:
            try:
                await self._check_all_devices()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Device health monitor error: {e}")
                await asyncio.sleep(30)

    def stop_monitoring(self):
        """Stop health monitoring"""
        self.running = False

    async def _check_all_devices(self):
        """Check health of all devices"""
        async with AsyncSessionLocal() as db:
            # Get all devices
            devices = (await db.execute(select(Device))).scalars().all()

            for device in devices:
                try:
                    health = await self._check_device_health(device)
                    await self._handle_health_status(health)
                except Exception as e:
                    logger.error(f"Error checking device {device.id}: {e}")

    async def _check_device_health(self, device: Device) -> DeviceHealthStatus:
        """Check individual device health"""
        issues = []
        status = "healthy"
        metrics = {}

        now = datetime.now(timezone.utc)

        # Check last seen time
        if device.last_seen:
            last_seen_delta = now - \
                device.last_seen.replace(tzinfo=timezone.utc)

            if last_seen_delta > timedelta(hours=24):
                status = "offline"
                issues.append("Device offline for >24h")
            elif last_seen_delta > timedelta(hours=1):
                status = "warning"
                issues.append("No heartbeat for >1h")
        else:
            status = "offline"
            issues.append("Never connected")

        # Check Redis presence
        if self.redis:
            try:
                presence = await self.redis.hgetall(f"presence:device:{device.id}")
                if presence:
                    # Parse capabilities and check for issues
                    if 'capabilities' in presence:
                        import json
                        try:
                            caps = json.loads(presence['capabilities'])
                            metrics['capabilities'] = caps

                            # Check for concerning capabilities
                            if caps.get('cpu_usage', 0) > 90:
                                issues.append("High CPU usage")
                                status = "warning"

                            if caps.get('memory_usage', 0) > 90:
                                issues.append("High memory usage")
                                status = "warning"

                            if caps.get('disk_usage', 0) > 95:
                                issues.append("Low disk space")
                                status = "critical"

                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass

        # Check task failure rate
        async with AsyncSessionLocal() as db:
            from app.models import Task

            # Recent tasks (last 24h)
            recent_cutoff = now - timedelta(hours=24)
            recent_tasks = (await db.execute(
                select(Task).where(
                    Task.device_id == device.id,
                    Task.created_at >= recent_cutoff.replace(tzinfo=None)
                )
            )).scalars().all()

            if recent_tasks:
                failed_count = sum(
                    1 for t in recent_tasks if t.status == "failed")
                failure_rate = failed_count / len(recent_tasks)

                metrics['recent_tasks'] = len(recent_tasks)
                metrics['failure_rate'] = failure_rate

                if failure_rate > 0.5:
                    issues.append(
                        f"High task failure rate: {failure_rate:.1%}")
                    status = "critical"
                elif failure_rate > 0.2:
                    issues.append(
                        f"Elevated task failure rate: {failure_rate:.1%}")
                    if status == "healthy":
                        status = "warning"

        return DeviceHealthStatus(
            device_id=str(device.id),
            user_id=str(device.user_id),
            device_name=device.device_name,
            status=status,
            last_seen=device.last_seen or datetime.min,
            issues=issues,
            metrics=metrics
        )

    async def _handle_health_status(self, health: DeviceHealthStatus):
        """Handle device health status changes"""

        # Store health status in Redis for API access
        if self.redis:
            health_key = f"device_health:{health.device_id}"
            await self.redis.hset(health_key, mapping={
                "status": health.status,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "issues": ",".join(health.issues),
                "metrics": str(health.metrics)
            })
            await self.redis.expire(health_key, 300)  # 5 min TTL

        # Alert on status changes
        if health.status in ("warning", "critical"):
            await notification_manager.notify_device_status(
                health.user_id,
                health.device_id,
                health.device_name,
                health.status
            )

            logger.warning(
                f"Device {health.device_name} ({health.device_id}) status: {health.status}, "
                f"issues: {health.issues}"
            )


# Global health monitor instance
health_monitor = DeviceHealthMonitor()

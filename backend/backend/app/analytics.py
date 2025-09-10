from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, Device, ActionLog, User, TaskStatus
from app.clients import get_redis


@dataclass
class PerformanceMetrics:
    avg_task_duration: float
    success_rate: float
    total_tasks: int
    device_utilization: float
    peak_hours: List[int]


@dataclass
class DeviceAnalytics:
    device_id: str
    device_name: str
    total_tasks: int
    success_rate: float
    avg_duration: float
    last_active: Optional[datetime]
    health_score: float


class AdvancedAnalytics:
    """Advanced analytics and performance metrics"""

    @staticmethod
    async def get_user_performance_summary(
        db: AsyncSession,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive performance summary for user"""

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_naive = cutoff.replace(tzinfo=None)

        # Total tasks and status breakdown
        total_tasks = await db.scalar(
            select(func.count(Task.id)).where(
                Task.user_id == user_id,
                Task.created_at >= cutoff_naive
            )
        ) or 0

        # Status breakdown
        status_breakdown = {}
        for status in TaskStatus:
            count = await db.scalar(
                select(func.count(Task.id)).where(
                    Task.user_id == user_id,
                    Task.status == status.value,
                    Task.created_at >= cutoff_naive
                )
            ) or 0
            status_breakdown[status.value] = count

        # Success rate
        completed = status_breakdown.get("completed", 0)
        failed = status_breakdown.get("failed", 0)
        success_rate = (completed / (completed + failed)) * \
            100 if (completed + failed) > 0 else 0

        # Average task duration (from creation to completion/failure)
        completed_tasks = (await db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.status.in_(["completed", "failed"]),
                Task.created_at >= cutoff_naive
            )
        )).scalars().all()

        durations = []
        for task in completed_tasks:
            if task.updated_at and task.created_at:
                duration = (task.updated_at - task.created_at).total_seconds()
                durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0

        # Device count and utilization
        device_count = await db.scalar(
            select(func.count(Device.id)).where(Device.user_id == user_id)
        ) or 0

        # Active devices (had tasks in last 7 days)
        week_ago = (datetime.now(timezone.utc) -
                    timedelta(days=7)).replace(tzinfo=None)
        active_devices = await db.scalar(
            select(func.count(func.distinct(Task.device_id))).where(
                Task.user_id == user_id,
                Task.created_at >= week_ago
            )
        ) or 0

        device_utilization = (active_devices / device_count) * \
            100 if device_count > 0 else 0

        # Peak hours analysis
        hourly_counts = {}
        for task in (await db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.created_at >= cutoff_naive
            )
        )).scalars().all():
            if task.created_at:
                hour = task.created_at.hour
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

        # Top 3 peak hours
        peak_hours = sorted(hourly_counts.items(),
                            key=lambda x: x[1], reverse=True)[:3]
        peak_hours = [hour for hour, count in peak_hours]

        # Recent trends (last 7 days vs previous 7 days)
        recent_week = (datetime.now(timezone.utc) -
                       timedelta(days=7)).replace(tzinfo=None)
        previous_week = (datetime.now(timezone.utc) -
                         timedelta(days=14)).replace(tzinfo=None)

        recent_tasks = await db.scalar(
            select(func.count(Task.id)).where(
                Task.user_id == user_id,
                Task.created_at >= recent_week
            )
        ) or 0

        previous_tasks = await db.scalar(
            select(func.count(Task.id)).where(
                Task.user_id == user_id,
                Task.created_at >= previous_week,
                Task.created_at < recent_week
            )
        ) or 0

        trend = "up" if recent_tasks > previous_tasks else "down" if recent_tasks < previous_tasks else "stable"
        trend_percentage = ((recent_tasks - previous_tasks) /
                            previous_tasks * 100) if previous_tasks > 0 else 0

        return {
            "period_days": days,
            "total_tasks": total_tasks,
            "status_breakdown": status_breakdown,
            "success_rate": round(success_rate, 2),
            "avg_duration_seconds": round(avg_duration, 2),
            "avg_duration_minutes": round(avg_duration / 60, 2),
            "device_count": device_count,
            "active_devices": active_devices,
            "device_utilization": round(device_utilization, 2),
            "peak_hours": peak_hours,
            "trend": {
                "direction": trend,
                "percentage": round(trend_percentage, 2),
                "recent_tasks": recent_tasks,
                "previous_tasks": previous_tasks
            }
        }

    @staticmethod
    async def get_device_analytics(
        db: AsyncSession,
        user_id: str,
        days: int = 30
    ) -> List[DeviceAnalytics]:
        """Get analytics for each user device"""

        cutoff = (datetime.now(timezone.utc) -
                  timedelta(days=days)).replace(tzinfo=None)

        # Get user devices with task stats
        devices = (await db.execute(
            select(Device).where(Device.user_id == user_id)
        )).scalars().all()

        analytics = []

        for device in devices:
            # Task counts
            total_tasks = await db.scalar(
                select(func.count(Task.id)).where(
                    Task.device_id == device.id,
                    Task.created_at >= cutoff
                )
            ) or 0

            completed_tasks = await db.scalar(
                select(func.count(Task.id)).where(
                    Task.device_id == device.id,
                    Task.status == "completed",
                    Task.created_at >= cutoff
                )
            ) or 0

            failed_tasks = await db.scalar(
                select(func.count(Task.id)).where(
                    Task.device_id == device.id,
                    Task.status == "failed",
                    Task.created_at >= cutoff
                )
            ) or 0

            success_rate = (completed_tasks / (completed_tasks + failed_tasks)
                            ) * 100 if (completed_tasks + failed_tasks) > 0 else 0

            # Average duration
            finished_tasks = (await db.execute(
                select(Task).where(
                    Task.device_id == device.id,
                    Task.status.in_(["completed", "failed"]),
                    Task.created_at >= cutoff
                )
            )).scalars().all()

            durations = []
            for task in finished_tasks:
                if task.updated_at and task.created_at:
                    duration = (task.updated_at -
                                task.created_at).total_seconds()
                    durations.append(duration)

            avg_duration = sum(durations) / len(durations) if durations else 0

            # Health score calculation
            health_score = 100.0

            # Reduce for low success rate
            if success_rate < 90:
                health_score -= (90 - success_rate)

            # Reduce for being offline too long
            if device.last_seen:
                offline_hours = (datetime.now(
                    timezone.utc) - device.last_seen.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                if offline_hours > 24:
                    health_score -= min(50, offline_hours - 24)
            else:
                health_score -= 50  # Never connected

            # Reduce for high task failure rate
            if total_tasks > 0:
                failure_rate = (failed_tasks / total_tasks) * 100
                if failure_rate > 10:
                    health_score -= (failure_rate - 10)

            health_score = max(0, min(100, health_score))

            analytics.append(DeviceAnalytics(
                device_id=str(device.id),
                device_name=device.device_name,
                total_tasks=total_tasks,
                success_rate=round(success_rate, 2),
                avg_duration=round(avg_duration, 2),
                last_active=device.last_seen,
                health_score=round(health_score, 2)
            ))

        return analytics

    @staticmethod
    async def get_action_performance(
        db: AsyncSession,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance breakdown by action type"""

        cutoff = (datetime.now(timezone.utc) -
                  timedelta(days=days)).replace(tzinfo=None)

        # Get all action logs for user's tasks
        action_logs = (await db.execute(
            select(ActionLog)
            .join(Task, Task.id == ActionLog.task_id)
            .where(
                Task.user_id == user_id,
                ActionLog.created_at >= cutoff
            )
        )).scalars().all()

        action_stats = {}

        for log in action_logs:
            action_type = log.action.get("type", "unknown")

            if action_type not in action_stats:
                action_stats[action_type] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                    "durations": []
                }

            action_stats[action_type]["total"] += 1

            # Check result status
            result = log.result or {}
            status = result.get("status", "unknown")

            if status in ("done", "ok", "success", "completed"):
                action_stats[action_type]["success"] += 1
            elif status in ("failed", "error"):
                action_stats[action_type]["failure"] += 1

            # Duration if available
            if "duration" in result:
                try:
                    duration = float(result["duration"])
                    action_stats[action_type]["durations"].append(duration)
                except (ValueError, TypeError):
                    pass

        # Calculate summary stats
        summary = {}
        for action_type, stats in action_stats.items():
            total = stats["total"]
            success = stats["success"]
            durations = stats["durations"]

            success_rate = (success / total) * 100 if total > 0 else 0
            avg_duration = sum(durations) / len(durations) if durations else 0

            summary[action_type] = {
                "total_executions": total,
                "success_rate": round(success_rate, 2),
                "avg_duration_seconds": round(avg_duration, 2),
                "fastest": round(min(durations), 2) if durations else 0,
                "slowest": round(max(durations), 2) if durations else 0
            }

        return summary

    @staticmethod
    async def get_system_health(db: AsyncSession) -> Dict[str, Any]:
        """Get overall system health metrics (admin only)"""

        now = datetime.now(timezone.utc)
        hour_ago = (now - timedelta(hours=1)).replace(tzinfo=None)
        day_ago = (now - timedelta(days=1)).replace(tzinfo=None)

        # Active users (had tasks in last 24h)
        active_users = await db.scalar(
            select(func.count(func.distinct(Task.user_id))).where(
                Task.created_at >= day_ago
            )
        ) or 0

        # Online devices
        redis = get_redis()
        online_devices = 0
        if redis:
            try:
                online_devices = await redis.scard("presence:online") or 0
            except Exception:
                pass

        # Task throughput (last hour)
        recent_tasks = await db.scalar(
            select(func.count(Task.id)).where(Task.created_at >= hour_ago)
        ) or 0

        # Error rate (last hour)
        recent_failures = await db.scalar(
            select(func.count(Task.id)).where(
                Task.created_at >= hour_ago,
                Task.status == "failed"
            )
        ) or 0

        error_rate = (recent_failures / recent_tasks) * \
            100 if recent_tasks > 0 else 0

        # Queue depth (pending/assigned tasks)
        queue_depth = await db.scalar(
            select(func.count(Task.id)).where(
                Task.status.in_(["queued", "assigned", "in_progress"])
            )
        ) or 0

        # Average response time (creation to assignment)
        recent_assigned = (await db.execute(
            select(Task).where(
                Task.status.in_(["assigned", "completed", "failed"]),
                Task.created_at >= day_ago
            )
        )).scalars().all()

        response_times = []
        for task in recent_assigned:
            if task.updated_at and task.created_at:
                response_time = (task.updated_at -
                                 task.created_at).total_seconds()
                response_times.append(response_time)

        avg_response_time = sum(response_times) / \
            len(response_times) if response_times else 0

        return {
            "timestamp": now.isoformat(),
            "active_users_24h": active_users,
            "online_devices": online_devices,
            "task_throughput_1h": recent_tasks,
            "error_rate_1h": round(error_rate, 2),
            "queue_depth": queue_depth,
            "avg_response_time_seconds": round(avg_response_time, 2),
            "system_status": "healthy" if error_rate < 5 and queue_depth < 100 else "degraded"
        }

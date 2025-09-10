from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta

from croniter import croniter
from loguru import logger
from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import ScheduledTask, Task, Device
from app.ai_safety import SafetyPolicy
from app.routers.notifications import notification_manager


class TaskScheduler:
    """Cron-like task scheduler"""

    def __init__(self):
        self.running = False
        self.check_interval = 60  # Check every minute

    async def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("Task scheduler started")

        while self.running:
            try:
                await self._check_and_run_scheduled_tasks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(30)

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Task scheduler stopped")

    async def _check_and_run_scheduled_tasks(self):
        """Check for scheduled tasks that need to run"""
        now = datetime.now(timezone.utc)
        # Convert to naive datetime for database comparison since DB stores naive datetimes
        now_naive = now.replace(tzinfo=None)

        async with AsyncSessionLocal() as db:
            # Get active scheduled tasks that are due
            scheduled_tasks = (await db.execute(
                select(ScheduledTask).where(
                    ScheduledTask.is_active == True,
                    (ScheduledTask.next_run <= now_naive) | (
                        ScheduledTask.next_run.is_(None))
                )
            )).scalars().all()

            for scheduled_task in scheduled_tasks:
                try:
                    await self._execute_scheduled_task(scheduled_task, db)
                except Exception as e:
                    logger.error(
                        f"Failed to execute scheduled task {scheduled_task.id}: {e}")

    async def _execute_scheduled_task(self, scheduled_task: ScheduledTask, db):
        """Execute a single scheduled task"""
        now = datetime.now(timezone.utc)
        # Convert to naive datetime for comparison since DB stores naive datetimes
        now_naive = now.replace(tzinfo=None)

        # Check if it's time to run
        if scheduled_task.next_run and scheduled_task.next_run > now_naive:
            return

        # Validate device exists and is accessible
        device = (await db.execute(
            select(Device).where(Device.id == scheduled_task.device_id)
        )).scalar_one_or_none()

        if not device:
            logger.warning(
                f"Device {scheduled_task.device_id} not found for scheduled task {scheduled_task.id}")
            return

        # Safety check on actions
        actions = scheduled_task.actions.get("actions", [])
        risk_level, risk_reasons = SafetyPolicy.analyze_actions(actions)

        # Skip critical risk tasks in scheduler (require manual approval)
        if SafetyPolicy.should_block(risk_level) or SafetyPolicy.requires_approval(risk_level):
            logger.warning(
                f"Scheduled task {scheduled_task.id} skipped due to {risk_level.value} risk: {risk_reasons}")
            await notification_manager.notify_user(
                str(scheduled_task.user_id),
                "scheduled_task_blocked",
                {
                    "scheduled_task_id": str(scheduled_task.id),
                    "name": scheduled_task.name,
                    "risk_level": risk_level.value,
                    "reasons": risk_reasons
                }
            )
            # Update next run time but don't execute
            scheduled_task.next_run = self._calculate_next_run(
                scheduled_task.cron_expression)
            await db.commit()
            return

        # Create and execute task
        import uuid
        task_id = uuid.uuid4().hex

        task = Task(
            id=task_id,
            user_id=scheduled_task.user_id,
            device_id=scheduled_task.device_id,
            status="queued",
            title=f"Scheduled: {scheduled_task.name}",
            description=f"Auto-generated from scheduled task '{scheduled_task.name}'",
            payload={
                "actions": actions,
                "scheduled_task_id": str(scheduled_task.id),
                "risk_analysis": {
                    "risk_level": risk_level.value,
                    "reasons": risk_reasons,
                    "requires_approval": False
                }
            },
        )

        db.add(task)

        # Update scheduled task stats
        scheduled_task.last_run = now_naive
        scheduled_task.run_count += 1
        scheduled_task.next_run = self._calculate_next_run(
            scheduled_task.cron_expression)

        await db.commit()

        # Publish task for delivery
        from app.routing import publish_task_envelope
        from app.security import sign_message_hmac

        envelope = {
            "type": "task.exec",
            "task_id": task_id,
            "issued_at": now.isoformat(),
            "actions": actions,
        }
        envelope["signature"] = sign_message_hmac(envelope)

        await publish_task_envelope(str(scheduled_task.device_id), envelope)

        logger.info(
            f"Executed scheduled task {scheduled_task.name} -> task {task_id}")

        # Notify user
        await notification_manager.notify_user(
            str(scheduled_task.user_id),
            "scheduled_task_executed",
            {
                "scheduled_task_id": str(scheduled_task.id),
                "task_id": task_id,
                "name": scheduled_task.name
            }
        )

    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression"""
        try:
            cron = croniter(cron_expression, datetime.now(timezone.utc))
            next_run = cron.get_next(datetime)
            return next_run.replace(tzinfo=None)
        except Exception as e:
            logger.error(f"Invalid cron expression '{cron_expression}': {e}")
            # Default to 1 hour from now
            return (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None)

    @staticmethod
    def validate_cron_expression(cron_expression: str) -> bool:
        """Validate cron expression format (5 fields only)"""
        try:
            # Check that it has exactly 5 fields
            fields = cron_expression.strip().split()
            if len(fields) != 5:
                return False

            # Test with current time
            cron = croniter(cron_expression, datetime.now())
            cron.get_next()  # This will raise exception if invalid
            return True
        except Exception:
            return False

    @staticmethod
    def get_cron_description(cron_expression: str) -> str:
        """Get human-readable description of cron expression"""
        try:
            # Simple descriptions for common patterns
            patterns = {
                "0 * * * *": "Every hour",
                "0 0 * * *": "Daily at midnight",
                "0 9 * * *": "Daily at 9 AM",
                "0 9 * * 1-5": "Weekdays at 9 AM",
                "0 0 * * 0": "Weekly on Sunday",
                "0 0 1 * *": "Monthly on 1st",
                "*/5 * * * *": "Every 5 minutes",
                "*/15 * * * *": "Every 15 minutes",
                "*/30 * * * *": "Every 30 minutes",
            }

            if cron_expression in patterns:
                return patterns[cron_expression]

            # Parse components
            parts = cron_expression.split()
            if len(parts) == 5:
                minute, hour, day, month, weekday = parts

                desc_parts = []
                if minute == "0":
                    desc_parts.append("at the top of the hour")
                elif minute != "*":
                    desc_parts.append(f"at minute {minute}")

                if hour != "*":
                    desc_parts.append(f"at {hour}:00")

                if day != "*":
                    desc_parts.append(f"on day {day}")

                if month != "*":
                    desc_parts.append(f"in month {month}")

                if weekday != "*":
                    days = {"0": "Sun", "1": "Mon", "2": "Tue",
                            "3": "Wed", "4": "Thu", "5": "Fri", "6": "Sat"}
                    if "-" in weekday:
                        start, end = weekday.split("-")
                        desc_parts.append(
                            f"from {days.get(start, start)} to {days.get(end, end)}")
                    else:
                        desc_parts.append(f"on {days.get(weekday, weekday)}")

                return " ".join(desc_parts) if desc_parts else "Custom schedule"

            return "Custom schedule"
        except Exception:
            return "Invalid schedule"


# Global scheduler instance
scheduler = TaskScheduler()

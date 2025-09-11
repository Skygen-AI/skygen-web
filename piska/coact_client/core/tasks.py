"""
Task execution engine

Handles task processing, action execution, and result reporting.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
import traceback

from coact_client.config.settings import settings

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status"""
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionStatus(str, Enum):
    """Action execution status"""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ActionResult:
    """Result of action execution"""
    action_id: str
    action: Dict[str, Any]
    status: ActionStatus
    result: Dict[str, Any]
    error: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "action_id": self.action_id,
            "action": self.action,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "timestamp": self.timestamp
        }


@dataclass
class TaskExecution:
    """Task execution context"""
    task_id: str
    actions: List[Dict[str, Any]]
    status: TaskStatus
    results: List[ActionResult]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": [r.to_dict() for r in self.results],
            "error": self.error,
        }


# Action handler type
ActionHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class TaskEngine:
    """Task execution engine"""

    def __init__(self):
        self.action_handlers: Dict[str, ActionHandler] = {}
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.max_concurrent_tasks = settings.device.max_concurrent_tasks
        self.task_timeout = 300  # 5 minutes default timeout

        # Security settings
        self.require_confirmation = settings.security.require_task_confirmation
        self.enable_shell_commands = settings.security.enable_shell_commands
        self.shell_whitelist = settings.security.shell_whitelist

        # Task completion callback
        self.on_task_completed: Optional[Callable[[
            TaskExecution], Awaitable[None]]] = None

    def register_action_handler(self, action_type: str, handler: ActionHandler) -> None:
        """Register action handler for specific action type"""
        self.action_handlers[action_type] = handler
        logger.debug(f"Registered action handler for: {action_type}")

    def unregister_action_handler(self, action_type: str) -> None:
        """Unregister action handler"""
        if action_type in self.action_handlers:
            del self.action_handlers[action_type]
            logger.debug(f"Unregistered action handler for: {action_type}")

    def get_supported_actions(self) -> List[str]:
        """Get list of supported action types"""
        return list(self.action_handlers.keys())

    async def process_task(self, task_data: Dict[str, Any]) -> None:
        """Process incoming task"""
        task_id = task_data.get("task_id")
        actions = task_data.get("actions", [])

        if not task_id:
            logger.error("Task missing task_id")
            return

        if task_id in self.active_tasks:
            logger.warning(f"Task {task_id} already processing")
            return

        if len(self.active_tasks) >= self.max_concurrent_tasks:
            logger.warning(
                f"Max concurrent tasks ({self.max_concurrent_tasks}) reached, rejecting task {task_id}")
            # Could implement queuing here
            return

        # Create task execution context
        task_execution = TaskExecution(
            task_id=task_id,
            actions=actions,
            status=TaskStatus.RECEIVED,
            results=[],
            started_at=datetime.now(timezone.utc)
        )

        self.active_tasks[task_id] = task_execution
        logger.info(f"Processing task {task_id} with {len(actions)} actions")

        # Execute task in background
        asyncio.create_task(self._execute_task(task_execution))

    async def _execute_task(self, task_execution: TaskExecution) -> None:
        """Execute task actions"""
        try:
            task_execution.status = TaskStatus.PROCESSING

            # Security check - require confirmation for dangerous actions
            if self.require_confirmation and self._requires_confirmation(task_execution.actions):
                logger.warning(
                    f"Task {task_execution.task_id} requires user confirmation")
                # For now, we'll skip confirmation and proceed
                # In production, you'd implement a confirmation mechanism

            # Execute each action
            for i, action in enumerate(task_execution.actions):
                action_id = action.get("action_id", f"action_{i}")
                action_type = action.get("type", "unknown")

                logger.info(
                    f"Executing action {action_id} ({action_type}) for task {task_execution.task_id}")

                try:
                    # Check if action type is supported
                    if action_type not in self.action_handlers:
                        result = ActionResult(
                            action_id=action_id,
                            action=action,
                            status=ActionStatus.FAILED,
                            result={},
                            error=f"Unsupported action type: {action_type}"
                        )
                    else:
                        # Add task_id to action for handlers that need it
                        action_with_task_id = action.copy()
                        action_with_task_id["task_id"] = task_execution.task_id

                        # Execute action with timeout
                        handler = self.action_handlers[action_type]
                        action_result = await asyncio.wait_for(
                            handler(action_with_task_id),
                            timeout=self.task_timeout
                        )

                        result = ActionResult(
                            action_id=action_id,
                            action=action,
                            status=ActionStatus.DONE,
                            result=action_result
                        )

                except asyncio.TimeoutError:
                    result = ActionResult(
                        action_id=action_id,
                        action=action,
                        status=ActionStatus.FAILED,
                        result={},
                        error="Action timeout"
                    )
                except Exception as e:
                    logger.error(f"Action {action_id} failed: {e}")
                    result = ActionResult(
                        action_id=action_id,
                        action=action,
                        status=ActionStatus.FAILED,
                        result={},
                        error=str(e)
                    )

                task_execution.results.append(result)

                # Stop on first failure if configured
                if result.status == ActionStatus.FAILED and not settings.debug:
                    logger.warning(
                        f"Stopping task {task_execution.task_id} due to failed action")
                    break

            # Determine overall task status
            failed_actions = [
                r for r in task_execution.results if r.status == ActionStatus.FAILED]
            if failed_actions:
                task_execution.status = TaskStatus.FAILED
                task_execution.error = f"{len(failed_actions)} actions failed"
            else:
                task_execution.status = TaskStatus.COMPLETED

            task_execution.completed_at = datetime.now(timezone.utc)

            logger.info(
                f"Task {task_execution.task_id} {task_execution.status.value}")

            # Call completion callback
            if self.on_task_completed:
                try:
                    await self.on_task_completed(task_execution)
                except Exception as e:
                    logger.error(f"Task completion callback error: {e}")

        except Exception as e:
            logger.error(f"Task execution error: {e}")
            logger.error(traceback.format_exc())

            task_execution.status = TaskStatus.FAILED
            task_execution.error = str(e)
            task_execution.completed_at = datetime.now(timezone.utc)

            if self.on_task_completed:
                try:
                    await self.on_task_completed(task_execution)
                except Exception as callback_error:
                    logger.error(
                        f"Task completion callback error: {callback_error}")

        finally:
            # Remove from active tasks
            if task_execution.task_id in self.active_tasks:
                del self.active_tasks[task_execution.task_id]

    def _requires_confirmation(self, actions: List[Dict[str, Any]]) -> bool:
        """Check if any actions require user confirmation"""
        dangerous_types = {"shell", "file_delete", "network_write", "system"}

        for action in actions:
            action_type = action.get("type")
            if action_type in dangerous_types:

                # Special check for shell commands
                if action_type == "shell":
                    command = action.get("command", "")
                    # Allow whitelisted commands
                    if any(command.startswith(allowed) for allowed in self.shell_whitelist):
                        continue
                    return True
                else:
                    return True

        return False

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel active task"""
        if task_id in self.active_tasks:
            task_execution = self.active_tasks[task_id]
            task_execution.status = TaskStatus.CANCELLED
            task_execution.completed_at = datetime.now(timezone.utc)
            task_execution.error = "Task cancelled"

            # Call completion callback
            if self.on_task_completed:
                try:
                    await self.on_task_completed(task_execution)
                except Exception as e:
                    logger.error(f"Task completion callback error: {e}")

            del self.active_tasks[task_id]
            logger.info(f"Task {task_id} cancelled")
            return True

        return False

    def get_active_tasks(self) -> List[str]:
        """Get list of active task IDs"""
        return list(self.active_tasks.keys())

    def get_task_status(self, task_id: str) -> Optional[TaskExecution]:
        """Get task execution status"""
        return self.active_tasks.get(task_id)


# Global task engine instance
task_engine = TaskEngine()

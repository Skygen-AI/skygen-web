"""
Logging configuration and utilities

Provides structured logging with file rotation, remote logging, and performance monitoring.
"""

import logging
import logging.handlers
import sys
import json
import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

import aiohttp

from coact_client.config.settings import settings

# Custom log levels
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


def trace(self, message, *args, **kwargs):
    """Add trace method to logger"""
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kwargs)


logging.Logger.trace = trace


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in {
                    "name", "msg", "args", "levelname", "levelno", "pathname",
                    "filename", "module", "exc_info", "exc_text", "stack_info",
                    "lineno", "funcName", "created", "msecs", "relativeCreated",
                    "thread", "threadName", "processName", "process", "message"
                }:
                    log_data[key] = value
        
        return json.dumps(log_data, default=str)


class RemoteLogHandler(logging.Handler):
    """Handler that sends logs to remote server"""
    
    def __init__(self, api_url: str, batch_size: int = 10, flush_interval: int = 30):
        super().__init__()
        self.api_url = api_url
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.log_buffer: list = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_flush = time.time()
        self._flush_task: Optional[asyncio.Task] = None
        self._shutdown = False
    
    def emit(self, record: logging.LogRecord) -> None:
        """Add record to buffer for remote sending"""
        if self._shutdown:
            return
        
        try:
            # Format record
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = {
                    "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                    "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                }
            
            self.log_buffer.append(log_entry)
            
            # Flush if buffer is full or interval exceeded
            current_time = time.time()
            if (len(self.log_buffer) >= self.batch_size or 
                current_time - self.last_flush >= self.flush_interval):
                self._schedule_flush()
                
        except Exception:
            self.handleError(record)
    
    def _schedule_flush(self) -> None:
        """Schedule async flush if not already running"""
        if self._flush_task is None or self._flush_task.done():
            try:
                loop = asyncio.get_event_loop()
                self._flush_task = loop.create_task(self._flush_logs())
            except RuntimeError:
                # No event loop running, skip remote logging
                pass
    
    async def _flush_logs(self) -> None:
        """Send buffered logs to remote server"""
        if not self.log_buffer or self._shutdown:
            return
        
        try:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=10)
                )
            
            # Get auth header
            from coact_client.core.auth import auth_client
            auth_header = auth_client.get_auth_header()
            if not auth_header:
                return  # Can't send without authentication
            
            # Prepare payload
            logs_to_send = self.log_buffer.copy()
            self.log_buffer.clear()
            self.last_flush = time.time()
            
            payload = {
                "logs": logs_to_send,
                "device_id": None,  # Will be filled by device manager if available
                "client_version": settings.app_version,
            }
            
            # Try to get device ID
            try:
                from coact_client.core.device import device_manager
                device_info = device_manager.get_device_info()
                if device_info:
                    payload["device_id"] = device_info.device_id
            except Exception:
                pass
            
            # Send logs
            url = f"{self.api_url}/v1/logs/ingest"
            headers = {"Authorization": auth_header}
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    # Put logs back in buffer on failure
                    self.log_buffer.extend(logs_to_send)
                    
        except Exception as e:
            # Put logs back in buffer on failure
            if 'logs_to_send' in locals():
                self.log_buffer.extend(logs_to_send)
    
    def close(self) -> None:
        """Close handler and flush remaining logs"""
        self._shutdown = True
        if self._flush_task and not self._flush_task.done():
            # Try to wait for final flush
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._final_flush())
            except RuntimeError:
                pass
        super().close()
    
    async def _final_flush(self) -> None:
        """Final flush and cleanup"""
        await self._flush_logs()
        if self.session and not self.session.closed:
            await self.session.close()


class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
        self.metrics: Dict[str, list] = {}
    
    def time_operation(self, operation_name: str):
        """Context manager for timing operations"""
        return TimedOperation(self, operation_name)
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a performance metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        metric_data = {
            "timestamp": time.time(),
            "value": value,
            "tags": tags or {}
        }
        
        self.metrics[name].append(metric_data)
        
        # Log metric
        self.logger.info(
            f"Metric recorded: {name}={value}",
            extra={"metric_name": name, "metric_value": value, "metric_tags": tags}
        )
        
        # Keep only recent metrics (last 1000 entries)
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def get_metrics(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get recorded metrics"""
        if name:
            return self.metrics.get(name, [])
        return self.metrics
    
    def clear_metrics(self, name: Optional[str] = None) -> None:
        """Clear metrics"""
        if name:
            self.metrics.pop(name, None)
        else:
            self.metrics.clear()


class TimedOperation:
    """Context manager for timing operations"""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.record_metric(
                f"operation_duration_{self.operation_name}",
                duration,
                {"operation": self.operation_name}
            )


def setup_logging() -> None:
    """Setup application logging"""
    log_config = settings.logging
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_config.level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(log_config.format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = settings.get_log_file()
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=log_config.max_file_size_mb * 1024 * 1024,
        backupCount=log_config.backup_count
    )
    
    if settings.environment == "development":
        file_formatter = logging.Formatter(log_config.format)
    else:
        file_formatter = StructuredFormatter()
    
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Remote logging handler (if enabled and not in development)
    if (log_config.enable_remote_logging and 
        settings.environment != "development"):
        try:
            remote_handler = RemoteLogHandler(settings.server.api_url)
            remote_handler.setLevel(logging.INFO)  # Only send INFO and above
            root_logger.addHandler(remote_handler)
        except Exception as e:
            logging.warning(f"Failed to setup remote logging: {e}")
    
    # Set specific logger levels
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized - Level: {log_config.level}, File: {log_file}",
        extra={
            "app_version": settings.app_version,
            "environment": settings.environment,
            "log_file": str(log_file)
        }
    )


# Global performance monitor
performance_monitor = PerformanceMonitor()
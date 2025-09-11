from __future__ import annotations

from prometheus_client import Counter, Gauge


# WebSocket metrics
ws_connections_total = Counter("ws_connections_total", "Total WebSocket connections accepted")
ws_connections_current = Gauge(
    "ws_connections_current", "Current number of active WebSocket connections"
)
ws_heartbeats_total = Counter(
    "ws_heartbeats_total", "Total number of heartbeats received from devices"
)


# Task metrics
tasks_created_total = Counter("tasks_created_total", "Total tasks created")
tasks_assigned_total = Counter("tasks_assigned_total", "Total tasks assigned/delivered to devices")
tasks_completed_total = Counter("tasks_completed_total", "Total tasks completed successfully")
tasks_failed_total = Counter("tasks_failed_total", "Total tasks that failed")


# DLQ metrics
dlq_messages_total = Counter("dlq_messages_total", "Total messages routed to the DLQ")

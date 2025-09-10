# Debug API

## Overview

The Debug API provides system monitoring and troubleshooting endpoints for development and production debugging. These endpoints offer detailed visibility into system state and performance.

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

**Note:** In production, these endpoints should be restricted to authorized users or disabled entirely for security.

## Endpoints

### GET /v1/debug/devices

List all devices with detailed status information.

**Query Parameters:**

- `include_presence` (optional) - Include Redis presence data (default: true)
- `limit` (optional) - Max results (default: 50, max: 200)

**Response (200):**

```json
[
  {
    "id": "device-uuid",
    "user_id": "user-uuid",
    "device_name": "MacBook Pro",
    "platform": "macOS",
    "capabilities": {
      "screenshot": true,
      "input": true,
      "file_system": false
    },
    "created_at": "2024-01-12T10:30:00Z",
    "last_seen": "2024-01-14T15:45:00Z",
    "connection_status": "online",
    "presence": {
      "device_id": "device-uuid",
      "connection_id": "conn_123",
      "node_id": "node_1",
      "status": "online",
      "last_seen": "2024-01-14T15:45:00Z"
    },
    "redis_online": true
  }
]
```

### GET /v1/debug/tasks/{task_id}

Get detailed information about a specific task.

**Response (200):**

```json
{
  "id": "task_123",
  "user_id": "user-uuid",
  "device_id": "device-uuid",
  "status": "completed",
  "title": "Debug Test Task",
  "description": "Task for debugging purposes",
  "payload": {
    "actions": [
      {
        "action_id": "1",
        "type": "screenshot",
        "params": {}
      }
    ]
  },
  "idempotency_key": "debug_idem_123",
  "created_at": "2024-01-14T14:00:00Z",
  "updated_at": "2024-01-14T14:02:00Z",
  "action_logs": [
    {
      "id": 12345,
      "action": "screenshot",
      "result": {
        "status": "success",
        "file_path": "screenshots/debug.png",
        "duration_ms": 1500
      },
      "actor": "system",
      "created_at": "2024-01-14T14:01:30Z"
    }
  ]
}
```

### GET /v1/debug/tasks

List tasks with filtering options for debugging.

**Query Parameters:**

- `status` (optional) - Filter by task status
- `device_id` (optional) - Filter by device ID (UUID format)
- `limit` (optional) - Max results (default: 20, max: 100)

**Response (200):**

```json
[
  {
    "id": "task_123",
    "user_id": "user-uuid",
    "device_id": "device-uuid",
    "status": "completed",
    "title": "Debug Test Task",
    "description": "Task for debugging",
    "created_at": "2024-01-14T14:00:00Z",
    "updated_at": "2024-01-14T14:02:00Z",
    "actions_count": 1
  }
]
```

### GET /v1/debug/system/stats

Get comprehensive system statistics.

**Response (200):**

```json
{
  "timestamp": "2024-01-14T16:00:00Z",
  "environment": "production",
  "node_id": "node_1",
  "counts": {
    "users": 1250,
    "devices": 3200,
    "tasks": 45600
  },
  "task_status_breakdown": {
    "created": 5,
    "queued": 12,
    "assigned": 8,
    "in_progress": 15,
    "completed": 45234,
    "failed": 312,
    "cancelled": 14
  },
  "recent_activity_24h": {
    "new_tasks": 156,
    "new_devices": 8
  },
  "redis": {
    "online_devices": 2847,
    "connected": true
  }
}
```

### GET /v1/debug/system/health

Detailed system health check with component status.

**Response (200):**

```json
{
  "timestamp": "2024-01-14T16:00:00Z",
  "overall": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "type": "postgresql"
    },
    "redis": {
      "status": "healthy",
      "type": "redis"
    },
    "task_processing": {
      "status": "warning",
      "stuck_tasks": 3,
      "message": "3 tasks stuck in progress for >1 hour"
    }
  }
}
```

**Overall Health Status:**

- `healthy` - All components functioning normally
- `degraded` - Some non-critical issues detected
- `unhealthy` - Critical components failing

**Component Status Values:**

- `healthy` - Component functioning normally
- `warning` - Component has issues but still functional
- `unhealthy` - Component failing or unavailable
- `not_configured` - Component not configured

### GET /v1/debug/presence/online

Get list of currently online device IDs from Redis.

**Response (200):**

```json
["device-uuid-1", "device-uuid-2", "device-uuid-3"]
```

### GET /v1/debug/logs/recent

Get recent action logs for debugging.

**Query Parameters:**

- `limit` (optional) - Max results (default: 50, max: 200)

**Response (200):**

```json
[
  {
    "id": 12345,
    "task_id": "task_123",
    "device_id": "device-uuid",
    "action": "screenshot",
    "result": {
      "status": "success",
      "duration_ms": 1500,
      "file_size": 245760
    },
    "actor": "system",
    "created_at": "2024-01-14T15:30:00Z"
  }
]
```

## Use Cases

### System Monitoring

- Monitor overall system health and performance
- Track component status and availability
- Identify resource usage patterns

### Troubleshooting

- Investigate task execution failures
- Debug device connectivity issues
- Analyze system bottlenecks

### Performance Analysis

- Monitor task processing times
- Identify stuck or slow operations
- Analyze system load patterns

### Development Support

- Debug integration issues
- Verify system configuration
- Test deployment health

## Redis Integration

Debug endpoints integrate with Redis for real-time system state:

### Presence Data

- Device online/offline status
- Connection metadata
- Heartbeat timestamps

### Performance Metrics

- Online device counts
- Connection health
- Cache performance

## Security Considerations

### Production Usage

- **Disable or restrict** debug endpoints in production
- **Implement IP whitelisting** for debug access
- **Log all debug endpoint access** for audit
- **Use separate authentication** for debug endpoints

### Data Exposure

- Debug endpoints may expose sensitive system information
- Consider data sanitization for production environments
- Implement appropriate access controls

### Rate Limiting

- Apply strict rate limits to prevent abuse
- Monitor for unusual debug endpoint usage
- Consider temporary disabling during incidents

## Error Responses

- `400` - Invalid parameters or malformed requests
- `404` - Resource not found
- `401` - Authentication required
- `500` - Internal server error
- `503` - Service unavailable (e.g., Redis down)

## Monitoring and Alerting

Use debug endpoints to implement monitoring:

### Health Checks

- Monitor `/debug/system/health` for component failures
- Alert on `degraded` or `unhealthy` overall status
- Track component-specific issues

### Performance Monitoring

- Monitor task processing metrics
- Track stuck task counts
- Analyze system load trends

### Capacity Planning

- Monitor user and device growth
- Track resource utilization
- Plan scaling based on trends

## Best Practices

### Development

- Use debug endpoints for local development and testing
- Implement comprehensive health checks
- Monitor system state during development

### Staging

- Use debug endpoints for deployment verification
- Test system health after updates
- Validate configuration changes

### Production

- **Restrict access** to authorized personnel only
- **Monitor usage** of debug endpoints
- **Disable if not needed** for security
- **Implement proper logging** of debug access

### Troubleshooting Workflow

1. Check overall system health
2. Review recent task and device activity
3. Investigate specific failing components
4. Analyze logs for error patterns
5. Monitor system recovery

# Scheduled Tasks API

## Overview

The Scheduled Tasks API allows users to create, manage, and execute tasks on a recurring schedule using cron expressions. Tasks can be based on templates and support variable substitution.

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

## Endpoints

### POST /v1/scheduled-tasks/

Create a new scheduled task.

**Request Body:**

```json
{
  "name": "Daily Screenshot",
  "cron_expression": "0 9 * * *",
  "actions": [
    {
      "action_id": "1",
      "type": "screenshot",
      "params": {}
    }
  ],
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "optional-template-uuid",
  "is_active": true
}
```

**Response (201):**

```json
{
  "id": "task-uuid",
  "name": "Daily Screenshot",
  "cron_expression": "0 9 * * *",
  "cron_description": "At 09:00 AM every day",
  "actions": [...],
  "is_active": true,
  "next_run": "2024-01-15T09:00:00",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": "template-uuid",
  "created_at": "2024-01-14T12:00:00Z"
}
```

**Cron Expression Format:**

- Standard 5-field cron: `minute hour day month weekday`
- Examples:
  - `0 9 * * *` - Every day at 9 AM
  - `*/15 * * * *` - Every 15 minutes
  - `0 0 1 * *` - First day of every month
  - `0 18 * * 1-5` - 6 PM on weekdays

### GET /v1/scheduled-tasks/

List user's scheduled tasks.

**Query Parameters:**

- `device_id` (optional) - Filter by device ID
- `is_active` (optional) - Filter by active status (true/false)
- `limit` (optional) - Max results (default: 50, max: 200)

**Response (200):**

```json
[
  {
    "id": "task-uuid",
    "name": "Daily Screenshot",
    "cron_expression": "0 9 * * *",
    "cron_description": "At 09:00 AM every day",
    "actions": [...],
    "is_active": true,
    "last_run": "2024-01-14T09:00:00",
    "next_run": "2024-01-15T09:00:00",
    "run_count": 5,
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "template_id": null,
    "created_at": "2024-01-10T12:00:00Z"
  }
]
```

### GET /v1/scheduled-tasks/{task_id}

Get a specific scheduled task.

**Response (200):**

```json
{
  "id": "task-uuid",
  "name": "Daily Screenshot",
  "cron_expression": "0 9 * * *",
  "cron_description": "At 09:00 AM every day",
  "actions": [...],
  "is_active": true,
  "last_run": "2024-01-14T09:00:00",
  "next_run": "2024-01-15T09:00:00",
  "run_count": 5,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_id": null,
  "created_at": "2024-01-10T12:00:00Z"
}
```

### PUT /v1/scheduled-tasks/{task_id}

Update a scheduled task.

**Request Body (partial update):**

```json
{
  "name": "Updated Task Name",
  "cron_expression": "0 15 * * *",
  "is_active": false
}
```

**Response (200):**

```json
{
  "id": "task-uuid",
  "name": "Updated Task Name",
  "cron_expression": "0 15 * * *",
  "cron_description": "At 03:00 PM every day",
  "actions": [...],
  "is_active": false,
  "next_run": "2024-01-15T15:00:00"
}
```

### DELETE /v1/scheduled-tasks/{task_id}

Delete a scheduled task.

**Response (200):**

```json
{
  "status": "deleted"
}
```

### POST /v1/scheduled-tasks/{task_id}/run

Manually trigger a scheduled task to run immediately.

**Response (200):**

```json
{
  "status": "triggered",
  "message": "Scheduled task will run within the next minute"
}
```

### POST /v1/scheduled-tasks/{task_id}/toggle

Toggle scheduled task active/inactive status.

**Response (200):**

```json
{
  "id": "task-uuid",
  "is_active": false,
  "status": "deactivated"
}
```

## Error Responses

- `400` - Invalid cron expression or request data
- `404` - Scheduled task or device not found
- `401` - Authentication required
- `403` - Access denied

## Cron Expression Validation

The system validates cron expressions and provides human-readable descriptions:

- **Valid formats:** 5-field cron expressions
- **Ranges:**
  - Minutes: 0-59
  - Hours: 0-23
  - Days: 1-31
  - Months: 1-12
  - Weekdays: 0-7 (0 and 7 are Sunday)
- **Special characters:** `*`, `,`, `-`, `/`

## Integration with Templates

Scheduled tasks can reference task templates for reusable automation:

1. Create a task template with variables
2. Reference the template in scheduled task creation
3. Variables are resolved when the task executes

## Execution Flow

1. Task scheduler evaluates cron expressions every minute
2. Tasks due for execution are queued
3. Tasks are delivered to target devices
4. Execution results update `last_run`, `next_run`, and `run_count`
5. Failed executions are logged but don't affect scheduling

## Best Practices

- Use descriptive names for scheduled tasks
- Test cron expressions before creating tasks
- Monitor task execution through logs
- Use templates for commonly repeated actions
- Set appropriate `is_active` status for maintenance

# Admin API

## Overview

The Admin API provides system administrators with endpoints to monitor users, devices, tasks, and system activity across the entire platform.

## Authentication

All endpoints require Bearer token authentication with admin privileges:

```
Authorization: Bearer <admin_access_token>
```

**Note:** These endpoints are restricted to users with admin privileges. Regular users will receive `403 Forbidden` responses.

## Endpoints

### GET /v1/admin/users

List all users in the system.

**Query Parameters:**

- `limit` (optional) - Max results (default: 50, max: 200)

**Response (200):**

```json
[
  {
    "id": "user-uuid",
    "email": "user@example.com",
    "is_active": true,
    "is_admin": false,
    "created_at": "2024-01-10T12:00:00Z"
  }
]
```

**Ordering:** Results are ordered by `created_at` descending (newest first).

### GET /v1/admin/devices

List all devices in the system.

**Query Parameters:**

- `limit` (optional) - Max results (default: 100, max: 500)

**Response (200):**

```json
[
  {
    "id": "device-uuid",
    "user_id": "user-uuid",
    "device_name": "MacBook Pro",
    "platform": "macOS",
    "created_at": "2024-01-12T10:30:00Z",
    "last_seen": "2024-01-14T15:45:00Z",
    "connection_status": "online"
  }
]
```

**Ordering:** Results are ordered by `created_at` descending (newest first).

### GET /v1/admin/tasks

List all tasks in the system.

**Query Parameters:**

- `status` (optional) - Filter by task status
- `limit` (optional) - Max results (default: 100, max: 500)

**Response (200):**

```json
[
  {
    "id": "task_123",
    "user_id": "user-uuid",
    "device_id": "device-uuid",
    "status": "completed",
    "title": "Screenshot Task",
    "created_at": "2024-01-14T14:00:00Z",
    "updated_at": "2024-01-14T14:02:00Z"
  }
]
```

**Valid Status Values:**

- `created` - Task created
- `queued` - Queued for execution
- `assigned` - Assigned to device
- `in_progress` - Currently executing
- `awaiting_confirmation` - Awaiting user approval
- `completed` - Successfully completed
- `failed` - Execution failed
- `cancelled` - Cancelled by user or system

**Ordering:** Results are ordered by `created_at` descending (newest first).

### GET /v1/admin/logs

List all action logs in the system.

**Query Parameters:**

- `limit` (optional) - Max results (default: 100, max: 500)

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
      "file_path": "screenshots/image.png"
    },
    "actor": "system",
    "created_at": "2024-01-14T14:01:30Z"
  }
]
```

**Ordering:** Results are ordered by `created_at` descending (newest first).

## Data Privacy and Security

### User Data Protection

- User passwords and sensitive data are never exposed
- Only essential user information is provided for administrative purposes
- Email addresses are included for user identification

### Access Control

- All endpoints require admin-level authentication
- Regular users cannot access any admin endpoints
- Failed admin access attempts should be logged for security monitoring

### Data Scope

Admin endpoints provide system-wide visibility:

- **Users:** All registered users across the platform
- **Devices:** All enrolled devices from all users
- **Tasks:** All tasks created by any user
- **Logs:** All action logs from all devices and tasks

## Use Cases

### System Monitoring

- Monitor user registration and activity patterns
- Track device enrollment and connection status
- Analyze task execution success rates and performance

### Troubleshooting

- Investigate failed tasks across the system
- Identify problematic devices or users
- Review action logs for debugging

### Platform Analytics

- Understand platform usage patterns
- Identify popular device platforms
- Monitor system load and capacity

### User Support

- Assist users with device or task issues
- Verify user account status and activity
- Investigate reported problems

## Rate Limiting

Admin endpoints may have different rate limits than regular API endpoints to support administrative workflows while preventing abuse.

## Monitoring and Alerting

Consider implementing monitoring for:

- High failure rates in tasks
- Unusual user activity patterns
- Device connection issues
- System performance metrics

## Error Responses

- `401` - Authentication required
- `403` - Admin privileges required
- `422` - Invalid query parameters
- `500` - Internal server error

## Best Practices

- Use appropriate pagination limits for large datasets
- Monitor admin API usage for security purposes
- Implement proper logging of admin actions
- Consider data retention policies for historical data
- Use filters to focus on relevant data subsets

## Security Considerations

- Admin access should be strictly controlled and monitored
- Consider implementing additional authentication factors for admin users
- Log all admin API access for audit purposes
- Regularly review admin user permissions
- Implement IP restrictions for admin access if possible

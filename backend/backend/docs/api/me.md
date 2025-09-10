# Me API

## Overview

The Me API provides user-specific endpoints for accessing profile information and recent activity. These endpoints allow users to view their own data and activity history.

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

## Endpoints

### GET /v1/me/profile

Get current user's profile information and statistics.

**Response (200):**

```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "is_email_verified": true,
  "created_at": "2024-01-01T10:00:00Z",
  "devices_count": 3,
  "tasks_count": 127
}
```

**Fields:**

- `id` - Unique user identifier
- `email` - User's email address
- `is_email_verified` - Email verification status
- `created_at` - Account creation timestamp
- `devices_count` - Total number of enrolled devices
- `tasks_count` - Total number of created tasks

### GET /v1/me/recent

Get user's recent activity including tasks and action logs.

**Response (200):**

```json
{
  "tasks": [
    {
      "id": "task_123",
      "device_id": "device-uuid",
      "status": "completed",
      "title": "Screenshot Task",
      "created_at": "2024-01-14T14:00:00Z",
      "updated_at": "2024-01-14T14:02:00Z"
    }
  ],
  "logs": [
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
}
```

**Data Limits:**

- `tasks` - Limited to 20 most recent tasks
- `logs` - Limited to 50 most recent action logs

**Ordering:**

- Tasks ordered by `created_at` descending (newest first)
- Logs ordered by `created_at` descending (newest first)

## Data Privacy

### User Isolation

- All endpoints return only the authenticated user's data
- Users cannot access other users' information
- Cross-user data leakage is prevented at the database level

### Data Scope

- Profile endpoint provides summary statistics
- Recent activity shows detailed task and log information
- Sensitive data (passwords, tokens) is never included

## Use Cases

### Profile Management

- Display user profile in applications
- Show account statistics and usage metrics
- Verify email verification status

### Activity Monitoring

- Recent task execution history
- Action log review for troubleshooting
- Personal activity dashboard

### Account Overview

- Quick view of account status and activity
- Usage statistics for personal tracking
- Recent activity for security monitoring

## Performance Considerations

### Caching

- Profile data may be cached for short periods
- Statistics are computed efficiently using database aggregations
- Recent activity uses optimized queries with limits

### Pagination

- Recent activity is automatically limited to prevent large responses
- For more historical data, use specific task or log APIs with pagination

## Integration with Other APIs

### Profile Statistics

Profile counts are consistent with:

- Device enrollment via `/v1/devices/enroll`
- Task creation via `/v1/tasks`

### Recent Activity

Recent activity includes:

- Tasks created via task APIs
- Action logs from task execution
- Results from device actions

## Error Responses

- `401` - Authentication required
- `500` - Internal server error

## Security Considerations

### Authentication

- All endpoints require valid Bearer token
- Token must belong to active user account
- Expired or invalid tokens are rejected

### Data Protection

- No sensitive information is exposed
- User data is isolated and protected
- Audit logging for access patterns

## Best Practices

### Client Implementation

- Cache profile data appropriately
- Refresh recent activity periodically
- Handle authentication errors gracefully

### Performance

- Don't poll these endpoints too frequently
- Use WebSocket notifications for real-time updates
- Implement proper error handling and retries

### User Experience

- Show loading states during data fetching
- Provide meaningful error messages
- Allow users to refresh data manually

## Rate Limiting

These endpoints may have generous rate limits as they serve user-facing applications, but implement reasonable limits to prevent abuse.

## Monitoring

Consider monitoring:

- Endpoint usage patterns
- Response times for performance
- Authentication failure rates
- Error rates and types

## Future Enhancements

Potential future additions:

- User preferences and settings
- More detailed activity filtering
- Export functionality for user data
- Activity analytics and insights

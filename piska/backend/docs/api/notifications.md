# Notifications API

## Overview

The Notifications API provides real-time WebSocket-based notifications for task updates, device status changes, and approval requests. This enables responsive user interfaces and immediate user feedback.

## Authentication

WebSocket connections require token-based authentication via query parameters:

```
wss://api.example.com/v1/notifications/ws/notifications?token=<access_token>
```

## WebSocket Endpoint

### Connection URL

```
/v1/notifications/ws/notifications
```

### Authentication

- Include `token` in query parameters
- Token must be valid Bearer access token
- Connection will be closed with code `4401` if authentication fails

### Connection Flow

1. **Client connects** with valid token in query parameters
2. **Server validates** token and user status
3. **Server accepts** connection and sends confirmation
4. **Heartbeat** mechanism maintains connection
5. **Notifications** are pushed to client as they occur

## Message Types

### Connection Confirmation

Sent immediately after successful connection:

```json
{
  "type": "connected",
  "timestamp": "2024-01-14T16:00:00Z"
}
```

### Heartbeat

Sent periodically to maintain connection:

```json
{
  "type": "heartbeat",
  "timestamp": "2024-01-14T16:00:00Z"
}
```

**Client Response:**
Send `"ping"` message to receive `"pong"` response.

### Task Updates

Sent when task status changes:

```json
{
  "type": "task_update",
  "timestamp": "2024-01-14T16:00:00Z",
  "data": {
    "task_id": "task_123",
    "status": "completed",
    "title": "Screenshot Task"
  }
}
```

**Status Values:**

- `queued` - Task queued for execution
- `assigned` - Task assigned to device
- `in_progress` - Task currently executing
- `completed` - Task completed successfully
- `failed` - Task execution failed
- `cancelled` - Task cancelled by user
- `approved` - Task approved for execution
- `rejected` - Task approval rejected
- `auto_cancelled` - Task auto-cancelled due to timeout

### Device Status

Sent when device online/offline status changes:

```json
{
  "type": "device_status",
  "timestamp": "2024-01-14T16:00:00Z",
  "data": {
    "device_id": "device-uuid",
    "device_name": "MacBook Pro",
    "status": "online"
  }
}
```

**Status Values:**

- `online` - Device connected and available
- `offline` - Device disconnected or unavailable

### Approval Needed

Sent when task requires user approval:

```json
{
  "type": "approval_needed",
  "timestamp": "2024-01-14T16:00:00Z",
  "data": {
    "task_id": "task_456",
    "title": "High Risk Task",
    "risk_reasons": ["file_system_access", "sensitive_file"]
  }
}
```

## Connection Management

### Multiple Connections

- Users can have multiple WebSocket connections (e.g., multiple browser tabs)
- All connections receive the same notifications
- Connections are managed independently

### Connection Cleanup

- Dead connections are automatically removed
- Failed message delivery removes connection from active set
- Proper cleanup prevents memory leaks

### Heartbeat Mechanism

- Server sends heartbeat every 30 seconds during inactivity
- Client can send `"ping"` to receive `"pong"` response
- Connection timeout after 60 seconds of inactivity

## Error Handling

### Authentication Errors

- **Code 4401:** Invalid or expired token
- **Code 4401:** User account inactive or not found
- **Code 4401:** Missing token parameter

### Connection Errors

- **Code 1000:** Normal closure
- **Code 1001:** Going away (server shutdown)
- **Code 1011:** Internal server error

### Message Delivery

- Failed message delivery removes connection
- No message queuing or retry mechanism
- Clients should reconnect on connection loss

## Client Implementation

### Basic Connection

```javascript
const token = "your_access_token";
const ws = new WebSocket(
  `wss://api.example.com/v1/notifications/ws/notifications?token=${token}`
);

ws.onopen = function (event) {
  console.log("Connected to notifications");
};

ws.onmessage = function (event) {
  const message = JSON.parse(event.data);
  handleNotification(message);
};

ws.onclose = function (event) {
  console.log("Disconnected:", event.code, event.reason);
  // Implement reconnection logic
};
```

### Message Handling

```javascript
function handleNotification(message) {
  switch (message.type) {
    case "connected":
      console.log("Connection confirmed");
      break;
    case "task_update":
      updateTaskStatus(message.data);
      break;
    case "device_status":
      updateDeviceStatus(message.data);
      break;
    case "approval_needed":
      showApprovalRequest(message.data);
      break;
    case "heartbeat":
      // Connection is alive
      break;
  }
}
```

### Heartbeat Implementation

```javascript
// Send ping every 25 seconds
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send("ping");
  }
}, 25000);

ws.onmessage = function (event) {
  if (event.data === "pong") {
    console.log("Heartbeat received");
    return;
  }
  // Handle other messages...
};
```

### Reconnection Logic

```javascript
function connectWithRetry() {
  const ws = new WebSocket(
    `wss://api.example.com/v1/notifications/ws/notifications?token=${token}`
  );

  ws.onclose = function (event) {
    if (event.code !== 1000) {
      // Not normal closure
      setTimeout(connectWithRetry, 5000); // Retry after 5 seconds
    }
  };

  return ws;
}
```

## Security Considerations

### Token Validation

- Tokens are validated on connection establishment
- Invalid tokens result in immediate connection closure
- Token expiration closes existing connections

### Data Privacy

- Users only receive notifications for their own data
- Cross-user notification leakage is prevented
- Sensitive data is not included in notifications

### Rate Limiting

- Connection establishment may be rate limited
- Message sending is controlled server-side
- Abuse detection and prevention

## Performance Considerations

### Scalability

- Server maintains in-memory connection registry
- Efficient message broadcasting to multiple connections
- Connection cleanup prevents memory leaks

### Message Volume

- Notifications are sent only for significant events
- No batching or queuing of messages
- Real-time delivery for immediate user feedback

### Resource Usage

- WebSocket connections consume server resources
- Idle connections maintained with minimal overhead
- Proper cleanup on disconnection

## Integration with Other Systems

### Task System

- Task status changes trigger notifications
- Integration with approval workflow
- Execution result notifications

### Device Management

- Device presence changes trigger notifications
- Connection status updates
- Health status changes

### Security System

- Approval requests for high-risk tasks
- Security event notifications
- Audit trail integration

## Best Practices

### Client-Side

- Implement proper reconnection logic
- Handle all message types gracefully
- Use heartbeat to detect connection issues
- Store connection state for UI updates

### Server-Side

- Validate all incoming connections
- Clean up dead connections promptly
- Monitor connection counts and performance
- Implement proper error handling

### Monitoring

- Track connection counts and patterns
- Monitor message delivery success rates
- Alert on connection failures or errors
- Log authentication failures for security

## Troubleshooting

### Common Issues

- **Connection refused:** Check token validity and format
- **Frequent disconnections:** Network issues or server problems
- **Missing notifications:** Check user permissions and data scope
- **Authentication failures:** Token expired or user inactive

### Debugging

- Enable WebSocket debugging in browser
- Check server logs for connection errors
- Verify token format and expiration
- Test connection with simple client

### Performance Issues

- Monitor connection count and server resources
- Check message delivery latency
- Analyze connection patterns and usage
- Optimize message content and frequency

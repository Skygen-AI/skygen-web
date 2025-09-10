# Webhooks API

## Overview

The Webhooks API allows users to register HTTP endpoints that receive real-time notifications about events in their account. This enables integration with external systems and custom automation workflows.

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

## Endpoints

### POST /v1/webhooks/

Create a new webhook.

**Request Body:**

```json
{
  "name": "Task Completion Webhook",
  "url": "https://your-app.com/webhook/tasks",
  "secret": "your-webhook-secret",
  "events": ["task.completed", "task.failed"]
}
```

**Fields:**

- `name` - Descriptive name for the webhook
- `url` - HTTP/HTTPS endpoint to receive webhook calls
- `secret` (optional) - Secret for HMAC signature verification
- `events` (optional) - Array of event types to subscribe to (default: empty)

**Response (201):**

```json
{
  "id": "webhook-uuid",
  "name": "Task Completion Webhook",
  "url": "https://your-app.com/webhook/tasks",
  "events": ["task.completed", "task.failed"],
  "created_at": "2024-01-14T16:00:00Z"
}
```

**Note:** The `secret` is not returned in responses for security.

### GET /v1/webhooks/

List user's webhooks.

**Response (200):**

```json
[
  {
    "id": "webhook-uuid",
    "name": "Task Completion Webhook",
    "url": "https://your-app.com/webhook/tasks",
    "events": ["task.completed", "task.failed"],
    "is_active": true,
    "created_at": "2024-01-14T16:00:00Z"
  }
]
```

### DELETE /v1/webhooks/{webhook_id}

Delete a webhook.

**Response (200):**

```json
{
  "status": "deleted"
}
```

## Event Types

### Task Events

- `task.completed` - Task successfully completed
- `task.failed` - Task execution failed
- `task.cancelled` - Task cancelled by user
- `task.approved` - Task approved for execution
- `task.rejected` - Task approval rejected

### Device Events

- `device.online` - Device came online
- `device.offline` - Device went offline
- `device.enrolled` - New device enrolled
- `device.removed` - Device removed from account

### System Events

- `system.maintenance` - System maintenance notifications
- `system.alert` - System alerts and warnings

### Wildcard Events

- `*` - Subscribe to all events

## Webhook Payload Format

All webhook calls use the following payload format:

```json
{
  "event": "task.completed",
  "timestamp": "2024-01-14T16:30:00Z",
  "data": {
    "task_id": "task_123",
    "status": "completed",
    "title": "Screenshot Task"
  }
}
```

**Common Fields:**

- `event` - The event type that triggered the webhook
- `timestamp` - ISO 8601 timestamp when the event occurred
- `data` - Event-specific data payload

### Task Event Data

```json
{
  "event": "task.completed",
  "timestamp": "2024-01-14T16:30:00Z",
  "data": {
    "task_id": "task_123",
    "status": "completed",
    "title": "Screenshot Task",
    "device_id": "device-uuid",
    "user_id": "user-uuid"
  }
}
```

### Device Event Data

```json
{
  "event": "device.online",
  "timestamp": "2024-01-14T16:30:00Z",
  "data": {
    "device_id": "device-uuid",
    "device_name": "MacBook Pro",
    "platform": "macOS",
    "user_id": "user-uuid"
  }
}
```

## Security

### HMAC Signature Verification

When a webhook includes a secret, requests are signed with HMAC-SHA256:

**Header:**

```
X-Webhook-Signature: sha256=<hmac_signature>
```

**Verification (Python):**

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

**Verification (Node.js):**

```javascript
const crypto = require("crypto");

function verifyWebhook(payload, signature, secret) {
  const expected = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");
  return crypto.timingSafeEqual(
    Buffer.from(`sha256=${expected}`),
    Buffer.from(signature)
  );
}
```

### Best Practices

- **Always verify signatures** when using secrets
- **Use HTTPS endpoints** for webhook URLs
- **Validate event data** before processing
- **Implement idempotency** to handle duplicate deliveries
- **Return 2xx status codes** for successful processing

## Delivery and Retries

### HTTP Request Details

- **Method:** POST
- **Content-Type:** application/json
- **User-Agent:** CoAct-Webhook/1.0
- **Timeout:** 10 seconds

### Retry Behavior

- **Success:** HTTP status 200-299
- **Failure:** HTTP status 400+ or network error
- **Retry attempts:** 3 total attempts
- **Retry delay:** Exponential backoff (1s, 2s, 4s)
- **Final failure:** Webhook delivery abandoned after 3 failures

### Response Requirements

Your webhook endpoint should:

- **Respond quickly** (< 10 seconds)
- **Return 2xx status** for successful processing
- **Return 4xx status** for permanent failures (no retry)
- **Return 5xx status** for temporary failures (will retry)

## Event Filtering

### Subscription Management

- Subscribe to specific events: `["task.completed", "device.online"]`
- Subscribe to all events: `["*"]`
- Empty array: No events delivered
- Events not in subscription list are filtered out

### Event Categories

- **Task events:** All events starting with `task.`
- **Device events:** All events starting with `device.`
- **System events:** All events starting with `system.`

## Implementation Examples

### Basic Webhook Handler (Python/Flask)

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your-webhook-secret"

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Verify signature
    signature = request.headers.get('X-Webhook-Signature')
    if signature:
        payload = request.get_data()
        expected = hmac.new(
            WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(f"sha256={expected}", signature):
            return jsonify({"error": "Invalid signature"}), 401

    # Process event
    event_data = request.json
    event_type = event_data.get('event')

    if event_type == 'task.completed':
        handle_task_completed(event_data['data'])
    elif event_type == 'device.online':
        handle_device_online(event_data['data'])

    return jsonify({"status": "ok"}), 200

def handle_task_completed(data):
    print(f"Task {data['task_id']} completed: {data['title']}")

def handle_device_online(data):
    print(f"Device {data['device_name']} is now online")
```

### Webhook Handler (Node.js/Express)

```javascript
const express = require("express");
const crypto = require("crypto");

const app = express();
const WEBHOOK_SECRET = "your-webhook-secret";

app.use(express.json());

app.post("/webhook", (req, res) => {
  // Verify signature
  const signature = req.headers["x-webhook-signature"];
  if (signature) {
    const payload = JSON.stringify(req.body);
    const expected = crypto
      .createHmac("sha256", WEBHOOK_SECRET)
      .update(payload)
      .digest("hex");

    if (
      !crypto.timingSafeEqual(
        Buffer.from(`sha256=${expected}`),
        Buffer.from(signature)
      )
    ) {
      return res.status(401).json({ error: "Invalid signature" });
    }
  }

  // Process event
  const { event, data } = req.body;

  switch (event) {
    case "task.completed":
      handleTaskCompleted(data);
      break;
    case "device.online":
      handleDeviceOnline(data);
      break;
  }

  res.json({ status: "ok" });
});

function handleTaskCompleted(data) {
  console.log(`Task ${data.task_id} completed: ${data.title}`);
}

function handleDeviceOnline(data) {
  console.log(`Device ${data.device_name} is now online`);
}
```

## Testing Webhooks

### Webhook Testing Tools

- **ngrok:** Expose local endpoints for testing
- **webhook.site:** Temporary webhook URLs for debugging
- **Postman:** Mock webhook endpoints
- **curl:** Manual webhook testing

### Test Payload Example

```bash
curl -X POST https://your-app.com/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=..." \
  -d '{
    "event": "task.completed",
    "timestamp": "2024-01-14T16:30:00Z",
    "data": {
      "task_id": "test_task",
      "status": "completed",
      "title": "Test Task"
    }
  }'
```

## Error Responses

- `400` - Invalid webhook data or URL
- `404` - Webhook not found
- `401` - Authentication required
- `403` - Access denied (not webhook owner)

## Rate Limiting

Webhook creation and management may be rate limited to prevent abuse. Webhook deliveries are not subject to API rate limits.

## Monitoring and Debugging

### Webhook Logs

- Delivery attempts and results are logged
- Failed deliveries include error details
- Retry attempts are tracked

### Debugging Tips

- Check webhook URL accessibility
- Verify HTTPS certificate validity
- Test signature verification logic
- Monitor response times and status codes
- Use webhook testing tools during development

## Best Practices

### Security

- Use HTTPS endpoints only
- Implement signature verification
- Validate all incoming data
- Use strong, unique secrets
- Rotate secrets periodically

### Reliability

- Implement idempotency for duplicate handling
- Use database transactions for consistency
- Handle retries gracefully
- Monitor webhook delivery success rates
- Implement proper error handling

### Performance

- Respond to webhooks quickly (< 10 seconds)
- Process heavy workloads asynchronously
- Use appropriate HTTP status codes
- Implement proper logging and monitoring
- Test webhook handlers under load

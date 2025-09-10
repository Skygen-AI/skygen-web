## WebSocket Device Gateway

### URL

`wss://gateway.example.com/v1/ws/agent`

### Register (client → server)

```json
{
  "type": "register",
  "device_id": "<uuid>",
  "device_token": "<jwt>",
  "capabilities": ["screenshot", "a11y", "input"]
}
```

Server validates JWT (`kid`, `exp`, `device_id`) and responds:

```json
{ "type": "register.ok" }
```

If invalid:

```json
{ "type": "register.error", "error": "invalid_token" }
```

### Heartbeat (client → server every ~30s)

```json
{ "type": "heartbeat", "device_id": "<uuid>", "timestamp": "<iso8601>" }
```

Server updates `presence:device:{id}` with TTL and `last_seen`; publishes `device.online`/`device.offline` via Redis.

### Task delivery (server → client)

```json
{
  "type": "task.exec",
  "task_id": "task_abc",
  "issued_at": "<iso8601>",
  "actions": [{ "action_id": "a1", "type": "screenshot", "params": {} }],
  "signature": "hmac-sha256(...)"
}
```

### Task result (client → server)

```json
{
  "type": "task.result",
  "task_id": "task_abc",
  "results": [
    {
      "action_id": "a1",
      "status": "done",
      "s3_url": "https://...",
      "meta": { "w": 1920, "h": 1080 }
    }
  ],
  "timestamp": "<iso8601>",
  "signature": "hmac-sha256(...)"
}
```

On device token revocation the server closes WS with code 4401 and logs audit.

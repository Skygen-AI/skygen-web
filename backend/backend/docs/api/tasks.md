## Tasks API

### POST /v1/tasks

Headers:

- `Authorization: Bearer <access_jwt>`
- `Idempotency-Key: <unique-id>`

Body:

```json
{
  "device_id": "<uuid>",
  "title": "Do things",
  "description": "optional",
  "metadata": {
    "actions": [{ "action_id": "a1", "type": "screenshot", "params": {} }]
  }
}
```

Response 201:

```json
{ "id": "task_abc", "status": "queued", "title": "Do things", "payload": {"actions": [...]}, "created_at": "...", "updated_at": "..." }
```

State machine: `created → queued → assigned → in_progress → awaiting_confirmation → completed | failed | cancelled`.

Server publishes `task.created` to Redis and attempts direct delivery to connected device.

Kafka events:

- `task.created` (payload: `task_id`, `device_id`, `user_id`, `actions`, `at`)
- `task.assigned` (worker emits when delivering)
- `task.dlq` (when offline/retries exceeded)

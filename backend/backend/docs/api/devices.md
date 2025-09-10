## Devices API

### POST /v1/devices/enroll

Auth: `Bearer <access_jwt>`
Body:

```json
{
  "device_name": "MacBook-01",
  "platform": "macOS",
  "capabilities": { "fs": true },
  "idempotency_key": "optional-key"
}
```

201 → `{ device_id, device_token, wss_url, kid, expires_at }`

Idempotency: identical body with same `idempotency_key` returns same `device_id`.

### POST /v1/devices/token/refresh

Body: `{ "device_id": "uuid" }`
200 → returns a fresh device token JWT

### POST /v1/devices/{device_id}/revoke

Revokes all active device tokens (closes WS on next check)
200 → `{ device_id, revoked_count }`

### Presence semantics

- Redis key `presence:device:{id}` (hash): `device_id`, `connection_id`, `node_id`, `status`, `last_seen`, `capabilities`.
- TTL refreshed on register/heartbeat. Missing heartbeat for > TTL → offline.
- Events published on `device.events`: `device.online`, `device.offline`.

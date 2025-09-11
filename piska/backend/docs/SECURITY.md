### Security Model

- Passwords: `passlib[bcrypt]`
- Access tokens: short-lived JWT (HS256), audience implicit (API)
- Refresh tokens: random opaque, hashed in DB, rotated on use
- Device tokens: HMAC-JWT with `kid` header; JTI stored per-device; revocation set in Redis
- Transport: terminate TLS at gateway; enforce HTTPS; HSTS at edge
- Rate limit + account lock: implement login rate limits; lock after threshold
- Audit logs: write immutable logs to ClickHouse with actor, subject, action

Key rotation:

- Maintain `DEVICE_JWT_KEYS` with `active_kid` and `keys`
- Rotate by adding new key, updating `active_kid`, revoking old JTIs as needed

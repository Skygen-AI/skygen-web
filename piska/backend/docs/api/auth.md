## Auth API

### POST /v1/auth/signup

Body:

```json
{ "email": "user@example.com", "password": "Password1!" }
```

201 Created → `{ id, email }`

### POST /v1/auth/login

Body:

```json
{ "email": "user@example.com", "password": "Password1!" }
```

200 OK → `{ "access_token", "refresh_token", "token_type": "bearer" }`

Rate limits and account lock:

- Per-IP and per-email attempts per minute
- Lock on repeated failures for `ACCOUNT_LOCK_MINUTES`

### POST /v1/auth/refresh

Body: raw refresh token string
200 OK → rotates and returns new `{ access_token, refresh_token }`

### Device tokens

- Device tokens are JWTs signed per `kid`. Active `kid` is rotated via config.
- Revocation list in Redis (`revoked_device_jti`) is enforced for WS sessions.

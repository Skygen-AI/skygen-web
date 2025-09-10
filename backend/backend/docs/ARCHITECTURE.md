### Architecture Overview

- **API**: FastAPI (async), JWT auth, rate-limited endpoints
- **DB**: PostgreSQL (SQLAlchemy 2.0 async)
- **Cache/Revocation**: Redis (device token revocation, idempotency cache optional)
- **Audit**: ClickHouse (append-only, immutable logs)
- **Agent**: Device connects via WebSocket with device JWT (kid, exp)
- **Scheduling**: Background task scheduler for automated workflows
- **Analytics**: Advanced performance monitoring and insights
- **Notifications**: Real-time WebSocket notifications and webhooks

Data flows:

1. User authenticates (access + rotating refresh tokens).
2. Device enrollment creates a `devices` row; returns device JWT and `wss_url`.
3. Agent connects to WS; server validates token (kid lookup) and revocation.
4. All actions logged to ClickHouse for audit.
5. Scheduled tasks execute based on cron expressions.
6. Analytics engine processes performance data and generates insights.
7. Real-time notifications delivered via WebSocket and webhooks.

Security highlights:

- Bcrypt password hashing, short-lived access JWT, opaque refresh tokens hashed in DB
- Rotating device JWT signing keys (kid-based). Revocation via Redis JTI sets
- Granular idempotency for enrollment via `idempotency_keys` table
- Task approval workflow for high-risk operations
- HMAC signature verification for webhooks
- Admin-only endpoints with privilege checking

## Device Gateway, Presence, and Routing

### Presence model

- Redis key `presence:device:{device_id}` (Hash)
  - `device_id`, `connection_id` (device token `jti`), `node_id`, `status` (online|offline), `last_seen` (ISO), `capabilities` (JSON string)
  - TTL refreshed on register and heartbeats; default 120s
- Redis set `presence:online` tracks currently online device ids for liveness sweeps
- On TTL expiry the presence watcher publishes `device.offline`

### Routing keys (cross-node delivery)

- Redis key `route:device:{device_id}` (Hash)
  - `connection_id` (jti), `node_id`, `updated_at`
  - TTL 120s; refreshed on WS register/heartbeat
- Purpose: declare which node is authoritative to deliver tasks to a device

### Delivery subscriber (per node)

- Subscribes to `deliver:task:*` (Pub/Sub pattern)
- On message:
  1. Extract `device_id` from channel, load `route:device:{device_id}`
  2. If `node_id` matches current node, fetch local WebSocket and send task envelope
  3. If not owner or no local WS, ignore (another node will deliver or device is offline)

### Message flows

1. Register (Device → Server)

   - `{ "type":"register", "device_id", "device_token", "capabilities":[] }`
   - Server: verify JWT (kid, exp, device_id), check revocation; reply `{ "type": "register.ok" }`
   - Update `presence:device:*` (TTL), add to `presence:online`, set `route:device:*`, emit `device.online`

2. Heartbeat (Device → Server)

   - `{ "type":"heartbeat", "device_id", "timestamp" }`
   - Server: refresh `last_seen`, TTL, and `route:device:*`; async update `devices.last_seen` in Postgres

3. Task delivery (Server → Device)

   - Envelope:
     - `{ "type":"task.exec", "task_id", "issued_at", "actions":[...], "signature":"hmac-sha256" }`
   - Producer (API) publishes to `deliver:task:{device_id}`; owning node delivers over WS

4. Task result (Device → Server)

   - `{ "type":"task.result", "task_id", "results":[...], "timestamp", "signature" }`
   - Server: optional HMAC verify, persist results (action_logs), set task status to completed/failed

5. Revocation (Admin → Server)
   - Revokes device token JTIs in Redis; WS background watcher closes with code 4401; audit logged

### Reconnection & idempotency

- Single active WS per `device_id`; new session closes the old one (stale)
- Pending tasks stored in DB; on successful register the node re-sends tasks with status in (queued, assigned)
- HTTP APIs are idempotent via `Idempotency-Key` header and `idempotency_keys` table

### Failure handling & backpressure

- Presence expiration marks device offline; delivery attempts are dropped if route does not match or WS is missing
- ClickHouse audit is best-effort; if unavailable, the system logs locally and continues
- Redis outages degrade presence/routing; WS still authenticates, but delivery is disabled until Redis returns

### Security considerations

- Device JWT HS256 with key rotation via `kid`; server selects secret by `kid`
- HMAC signatures on task envelopes and results (canonical JSON) mitigate tampering in transit at the WS layer
- Server-side policy engine (future work) validates payload/actions before enqueue
- Revocation lists (`revoked_device_jti`) are polled server-side to terminate revoked sessions

### Scaling & HA

- Stateless API/WS nodes behind a load balancer
- Redis as the single coordination point for presence and routing; Redis Cluster or replica set recommended
- Postgres for durable state (users, devices, tasks); use read replicas if needed
- ClickHouse for append-only audit, horizontally scalable

### Data schema (key tables)

- `users(id, email, password_hash, created_at, is_email_verified, is_active, ...)`
- `devices(id, user_id, platform, capabilities, created_at, last_seen, connection_status, device_token_kid)`
- `tasks(id, user_id, device_id, status, title, description, payload, idempotency_key, created_at, updated_at)`
- `action_logs(id, task_id, device_id, action, result, actor, created_at)`
- `idempotency_keys(id, user_id, endpoint, idem_key, resource_type, resource_id, request_body_hash, created_at)`
- `scheduled_tasks(id, user_id, device_id, template_id, name, cron_expression, actions, variables, is_active, next_run, last_run, run_count, created_at, updated_at)`
- `task_templates(id, user_id, name, description, category, actions, variables, is_public, usage_count, created_at, updated_at)`
- `webhooks(id, user_id, name, url, secret, events, is_active, created_at)`

## Extended Architecture Components

### Task Scheduling System

The scheduling system provides automated task execution based on cron expressions:

**Components:**

- **TaskScheduler**: Background service that evaluates cron expressions
- **ScheduledTask**: Database model storing recurring task definitions
- **Cron Engine**: Calculates next execution times and manages task lifecycle

**Flow:**

1. User creates scheduled task with cron expression
2. Scheduler evaluates due tasks every minute
3. Due tasks are queued for execution like regular tasks
4. Execution results update run statistics and next execution time

**Integration:**

- Uses existing task execution pipeline
- Supports template-based task generation
- Integrates with approval workflow for high-risk scheduled tasks

### Template System

Task templates enable reusable automation workflows with variable substitution:

**Features:**

- Variable substitution using `{{variable_name}}` syntax
- Public/private template sharing
- Usage tracking and popularity metrics
- Category-based organization

**Integration:**

- Templates can be used in scheduled tasks
- Variable values resolved at execution time
- Supports complex nested variable structures

### Analytics Engine

Advanced analytics provide performance insights and recommendations:

**Metrics Tracked:**

- Task success rates and execution times
- Device utilization and health scores
- Action-specific performance data
- Usage patterns and trends

**Components:**

- **AdvancedAnalytics**: Core analytics processing service
- **Performance Calculator**: Computes health scores and trends
- **Insight Generator**: AI-powered recommendations engine

**Data Sources:**

- Task execution history
- Device connectivity data
- Action logs and timing data
- User activity patterns

### Approval Workflow

Security-focused approval system for high-risk operations:

**Risk Assessment:**

- Automated risk analysis based on action types
- Configurable risk thresholds and rules
- Pattern matching for sensitive operations

**Approval Flow:**

1. High-risk tasks marked as `awaiting_confirmation`
2. User receives real-time notification
3. User approves/rejects via API or UI
4. Auto-cancellation after timeout (1 hour default)

**Integration:**

- Real-time notifications via WebSocket
- Audit logging of all approval decisions
- Webhook notifications for external systems

### Real-time Notifications

Multi-channel notification system for immediate user feedback:

**Channels:**

- **WebSocket**: Real-time browser notifications
- **Webhooks**: HTTP callbacks to external systems
- **Future**: Email, SMS, push notifications

**Event Types:**

- Task status changes (completed, failed, approved)
- Device status changes (online, offline)
- System alerts and maintenance notifications

**Features:**

- Multiple concurrent connections per user
- Automatic connection cleanup and reconnection
- HMAC signature verification for webhooks
- Retry logic with exponential backoff

### Admin and Debug Systems

Comprehensive monitoring and troubleshooting capabilities:

**Admin Features:**

- System-wide user, device, and task monitoring
- Cross-user visibility for support and debugging
- System health and performance metrics
- Audit trail access and analysis

**Debug Features:**

- Detailed system state inspection
- Task execution debugging and tracing
- Device connectivity troubleshooting
- Performance profiling and optimization

### Security Enhancements

Extended security model with multiple layers:

**Authentication & Authorization:**

- JWT-based access tokens with refresh rotation
- Admin privilege checking and enforcement
- Device-specific token management with revocation

**Data Protection:**

- User data isolation and privacy controls
- Sensitive data filtering in responses
- Audit logging of all administrative actions

**Risk Management:**

- Automated risk assessment for task approval
- Configurable security policies and thresholds
- Real-time security event monitoring

### Integration Architecture

**External System Integration:**

- **Webhooks**: HTTP callbacks for event notifications
- **REST APIs**: Comprehensive API coverage for all functionality
- **WebSocket**: Real-time bidirectional communication
- **Template Sharing**: Community-driven template marketplace

**Internal Service Communication:**

- **Event-driven**: Pub/sub patterns for loose coupling
- **Async Processing**: Non-blocking operations for scalability
- **Caching**: Redis for performance optimization
- **Background Jobs**: Scheduled and queued task processing

## Coact Backend

Coact is a secure, auditable "smart RPA" layer that executes actions on real user devices. It combines AI-assisted workflows with strict policy enforcement, device-local execution, and immutable audit logs.

Core pillars:

- Safety by default (policy engine, revocation, short-lived tokens)
- Reality-grade device access (local files, native apps, peripherals)
- Verifiable actions (immutable audit in ClickHouse)
- Automated scheduling and template-based workflows
- Real-time monitoring and performance analytics
- Comprehensive approval workflow for high-risk operations

## Features

### Core Functionality

- **Task Execution**: Execute automation tasks on enrolled devices
- **Device Management**: Enroll and manage devices with real-time presence
- **User Authentication**: JWT-based authentication with refresh tokens

### Advanced Features

- **Scheduled Tasks**: Automated task execution with cron expressions
- **Task Templates**: Reusable templates with variable substitution
- **Performance Analytics**: Comprehensive performance monitoring and insights
- **Approval Workflow**: Security-focused approval system for high-risk operations
- **Real-time Notifications**: WebSocket and webhook-based notifications
- **Admin Tools**: System monitoring and debugging capabilities

### Security & Compliance

- **Risk Assessment**: Automated analysis of task security implications
- **Audit Logging**: Immutable audit trail in ClickHouse
- **Token Management**: Secure device token lifecycle with revocation
- **Data Privacy**: User data isolation and access controls

## API Documentation

### Core APIs

- [Authentication](api/auth.md) - User login, signup, and token management
- [Devices](api/devices.md) - Device enrollment and management
- [Tasks](api/tasks.md) - Task creation and execution
- [Artifacts](api/artifacts.md) - File upload and management
- [WebSocket](api/ws.md) - Real-time device communication

### Extended APIs

- [Scheduled Tasks](api/scheduled_tasks.md) - Automated recurring tasks
- [Templates](api/templates.md) - Reusable task templates
- [Analytics](api/analytics.md) - Performance metrics and insights
- [Approvals](api/approvals.md) - Task approval workflow
- [Notifications](api/notifications.md) - Real-time notifications
- [Webhooks](api/webhooks.md) - HTTP callback integrations
- [Me](api/me.md) - User profile and activity
- [Admin](api/admin.md) - System administration (admin only)
- [Debug](api/debug.md) - System debugging and monitoring

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design including:

- Device gateway and presence management
- Task scheduling and execution pipeline
- Analytics engine and performance monitoring
- Security model and approval workflow
- Real-time notification system

## Operations

- [Deployment](ops/deployment.md) - Production deployment guide
- [Observability](ops/observability.md) - Monitoring and alerting
- [Broker](ops/broker.md) - Message broker configuration

## Security

- [Security Model](SECURITY.md) - Security architecture and controls
- [Threat Model](THREAT_MODEL.md) - Security threat analysis
- [Key Rotation](runbooks/key_rotation.md) - Key management procedures

## Quick start:

1. `cp .env.example .env` and adjust secrets
2. `docker compose up -d postgres redis clickhouse`
3. `uvicorn app.main:app --reload`
4. Visit `/docs` for the OpenAPI UI

## Testing

The backend includes comprehensive test suites:

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end API testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization testing

Run tests with:

```bash
cd backend
pytest tests/ -v
```

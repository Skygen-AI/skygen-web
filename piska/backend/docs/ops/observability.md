## Observability & Audit

Metrics:

- Request latency, error rates
- WS connections, disconnect reasons, revocation events

Logs:

- Application logs with trace IDs
- Audit logs in ClickHouse (action, actor, subject, metadata)

Kafka:

- Monitor topics via Redpanda admin (9644) or `rpk` CLI
- Watch `task.created`, `task.assigned`, and DLQ rates

Dashboards:

- Create dashboards for enrollment rates, revocations, auth failures

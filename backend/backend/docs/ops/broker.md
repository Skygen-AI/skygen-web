## Broker & Worker Behavior

### Topics

- `task.created` — produced by API upon task creation
- `task.assigned` — produced by worker upon delivery
- `task.dlq` — failed deliveries or offline devices (after retries)
- `device.{id}.commands` — optional per-device topic (future)

### Worker (Assigner)

1. Consume `task.created`
2. Check presence in Redis (`presence:online` and `route:device:{id}`)
3. If online → deliver `task.exec` via WS routing; publish `task.assigned`
4. If offline → retry with backoff or send to `task.dlq`

### Retries & DLQ

- Use exponential backoff (e.g., 1s, 5s, 15s, 60s) up to N attempts
- On exceed → emit to DLQ for manual inspection

### Operations

- Redpanda admin API (9644) or `rpk` for topic management
- Observability: track event rates and DLQ size

## Deployment

Dependencies: PostgreSQL, Redis, ClickHouse, Kafka (Redpanda), MinIO.

Environment:

- `DATABASE_URL`, `REDIS_URL`, `CLICKHOUSE_URL`
- `KAFKA_BROKERS` (e.g., `redpanda:9092`)
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `ARTIFACTS_BUCKET`
- Secrets: `ACCESS_TOKEN_SECRET`, `REFRESH_TOKEN_SECRET`, `DEVICE_JWT_KEYS`

Steps:

1. Run DB migrations (Alembic TBD)
2. Deploy FastAPI app (Uvicorn/Gunicorn behind Nginx/ALB)
3. Enforce TLS at the edge; HSTS
4. Configure health checks `/healthz`

Scalability:

- Stateless API; horizontal scaling
- Redis for revocation lists
- ClickHouse for append-only audit
- Kafka for task events, MinIO for artifacts

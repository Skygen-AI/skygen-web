## Artifacts API

### POST /v1/artifacts/presign

Auth: `Bearer <access_jwt>`

Body:

```json
{ "task_id": "task_abc", "filename": "s.png", "size": 123456 }
```

Response 200:

```json
{
  "upload_url": "https://minio...",
  "s3_url": "s3://coact-artifacts/tasks/task_abc/.../s.png",
  "expires_at": "<iso8601>"
}
```

Flow:

- Device запрашивает presigned PUT и загружает напрямую в MinIO.
- В `task.result` агент указывает `s3_url` артефакта.

Security:

- Ссылка короткоживущая (по умолчанию 5 минут), действует только на конкретный объект/размер.

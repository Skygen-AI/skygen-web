# Chat API

API для работы с чат-сессиями и сообщениями.

## Endpoints

### POST /v1/chat/sessions

Создание новой чат-сессии.

**Auth**: Bearer token required

**Body**:

```json
{
  "title": "My Chat Session",
  "device_id": "uuid-optional",
  "metadata": {}
}
```

**Response** (201):

```json
{
  "id": "session-uuid",
  "user_id": "user-uuid",
  "device_id": "device-uuid",
  "title": "My Chat Session",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "is_active": true,
  "metadata": {},
  "message_count": 0
}
```

### GET /v1/chat/sessions

Получение списка чат-сессий пользователя.

**Auth**: Bearer token required

**Query Parameters**:

- `limit`: int (default: 50, max: 100)
- `offset`: int (default: 0)
- `active_only`: bool (default: true)

**Response** (200):

```json
[
  {
    "id": "session-uuid",
    "user_id": "user-uuid",
    "device_id": "device-uuid",
    "title": "My Chat Session",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "is_active": true,
    "metadata": {},
    "message_count": 5
  }
]
```

### GET /v1/chat/sessions/{session_id}

Получение чат-сессии с сообщениями.

**Auth**: Bearer token required

**Response** (200):

```json
{
  "id": "session-uuid",
  "user_id": "user-uuid",
  "device_id": "device-uuid",
  "title": "My Chat Session",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "is_active": true,
  "metadata": {},
  "messages": [
    {
      "id": "message-uuid",
      "session_id": "session-uuid",
      "role": "user",
      "content": "Hello!",
      "created_at": "2024-01-01T12:00:00Z",
      "metadata": {},
      "task_id": null
    },
    {
      "id": "message-uuid-2",
      "session_id": "session-uuid",
      "role": "assistant",
      "content": "Hi! How can I help you?",
      "created_at": "2024-01-01T12:01:00Z",
      "metadata": {},
      "task_id": null
    }
  ]
}
```

### POST /v1/chat/sessions/{session_id}/messages

Добавление сообщения в чат.

**Auth**: Bearer token required

**Body**:

```json
{
  "content": "Hello, world!",
  "role": "user",
  "metadata": {}
}
```

**Response** (201):

```json
{
  "id": "message-uuid",
  "session_id": "session-uuid",
  "role": "user",
  "content": "Hello, world!",
  "created_at": "2024-01-01T12:00:00Z",
  "metadata": {},
  "task_id": null
}
```

### PUT /v1/chat/sessions/{session_id}

Обновление чат-сессии.

**Auth**: Bearer token required

**Body** (все поля опциональные):

```json
{
  "title": "Updated Title",
  "is_active": false,
  "metadata": { "updated": true }
}
```

**Response** (200):

```json
{
  "id": "session-uuid",
  "user_id": "user-uuid",
  "device_id": "device-uuid",
  "title": "Updated Title",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z",
  "is_active": false,
  "metadata": { "updated": true },
  "message_count": 10
}
```

### DELETE /v1/chat/sessions/{session_id}

Удаление чат-сессии.

**Auth**: Bearer token required

**Response** (200):

```json
{
  "message": "Chat session deleted successfully"
}
```

### GET /v1/chat/sessions/{session_id}/messages

Получение сообщений чата с пагинацией.

**Auth**: Bearer token required

**Query Parameters**:

- `limit`: int (default: 100, max: 500)
- `offset`: int (default: 0)

**Response** (200):

```json
[
  {
    "id": "message-uuid",
    "session_id": "session-uuid",
    "role": "user",
    "content": "Message content",
    "created_at": "2024-01-01T12:00:00Z",
    "metadata": {},
    "task_id": "task-id-if-linked"
  }
]
```

## Message Roles

- `user`: Сообщение от пользователя
- `assistant`: Ответ AI агента
- `system`: Системное сообщение

## Error Responses

### 404 Not Found

```json
{
  "detail": "Chat session not found"
}
```

### 400 Bad Request

```json
{
  "detail": "Chat session is not active"
}
```

## Features

- **Сохранение истории**: Все сообщения сохраняются в базе данных
- **Пагинация**: Поддержка больших чатов с пагинацией
- **Связь с задачами**: Сообщения могут быть связаны с созданными задачами
- **Метаданные**: Дополнительная информация для сообщений и сессий
- **Устройства**: Привязка чата к конкретному устройству
- **Активность**: Возможность архивирования старых чатов

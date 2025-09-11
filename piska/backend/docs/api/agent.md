# Agent API

API для взаимодействия с AI агентом, который может создавать задачи из чат-сообщений.

## Endpoints

### POST /v1/agent/chat

Основной endpoint для общения с AI агентом.

**Auth**: Bearer token required

**Body**:

```json
{
  "message": "Сделай скриншот экрана",
  "session_id": "session-uuid-optional",
  "device_id": "device-uuid-optional",
  "metadata": {}
}
```

**Response** (200):

```json
{
  "session_id": "session-uuid",
  "message": {
    "id": "message-uuid",
    "session_id": "session-uuid",
    "role": "user",
    "content": "Сделай скриншот экрана",
    "created_at": "2024-01-01T12:00:00Z",
    "metadata": {},
    "task_id": "task_abc123"
  },
  "assistant_message": {
    "id": "assistant-message-uuid",
    "session_id": "session-uuid",
    "role": "assistant",
    "content": "Понял! Я создал задачу для выполнения вашего запроса. Задача #task_abc123 будет выполнена на подключенном устройстве.",
    "created_at": "2024-01-01T12:00:01Z",
    "metadata": {
      "task_created": true,
      "task_id": "task_abc123",
      "generated_by": "simple_agent"
    },
    "task_id": null
  },
  "task_created": true,
  "task_id": "task_abc123"
}
```

### GET /v1/agent/capabilities

Получение информации о возможностях агента.

**Auth**: Bearer token required

**Response** (200):

```json
{
  "capabilities": [
    {
      "name": "screenshot",
      "description": "Take screenshots of the desktop",
      "keywords": ["screenshot", "скриншот", "снимок экрана"],
      "example": "Сделай скриншот экрана"
    },
    {
      "name": "click",
      "description": "Click at specific coordinates or elements",
      "keywords": ["click", "кликни", "нажми", "клик"],
      "example": "Кликни на кнопку"
    },
    {
      "name": "type_text",
      "description": "Type text using keyboard",
      "keywords": ["type", "напечатай", "введи", "набери"],
      "example": "Напечатай 'Hello World'"
    },
    {
      "name": "window_management",
      "description": "Open, close, and manage application windows",
      "keywords": ["open", "close", "открой", "закрой"],
      "example": "Открой браузер"
    },
    {
      "name": "search",
      "description": "Find files, applications, or elements",
      "keywords": ["find", "найди", "поиск"],
      "example": "Найди файл document.pdf"
    }
  ],
  "supported_languages": ["ru", "en"],
  "version": "1.0.0",
  "agent_type": "simple_rule_based"
}
```

## Agent Capabilities

Агент может понимать и выполнять следующие типы команд:

### 1. Скриншоты

**Ключевые слова**: screenshot, скриншот, снимок экрана

**Примеры**:

- "Сделай скриншот"
- "Take a screenshot"
- "Снимок экрана, пожалуйста"

**Результат**: Создается задача с действием `screenshot`

### 2. Клики

**Ключевые слова**: click, кликни, нажми, клик

**Примеры**:

- "Кликни на кнопку"
- "Click here"
- "Нажми на ссылку"

**Результат**: Создается задача с действием `CLICK`

### 3. Ввод текста

**Ключевые слова**: type, напечатай, введи, набери

**Примеры**:

- "Напечатай 'Hello World'"
- "Type some text"
- "Введи мой email"

**Результат**: Создается задача с действием `type_text`

### 4. Управление окнами

**Ключевые слова**: open, close, открой, закрой

**Примеры**:

- "Открой браузер"
- "Close the window"
- "Закрой приложение"

**Результат**: Создается общая задача (обычно начинается со скриншота)

### 5. Поиск

**Ключевые слова**: find, найди, поиск

**Примеры**:

- "Найди файл document.pdf"
- "Find Chrome browser"
- "Поиск в папке"

**Результат**: Создается общая задача для поиска

## Behavior

### Создание сессий

- Если `session_id` не передан, создается новая сессия автоматически
- Если передан несуществующий `session_id`, возвращается 404
- Сессии привязываются к пользователю

### Создание задач

- Задачи создаются только если:
  - Сообщение содержит ключевые слова команд
  - Указан `device_id` для выполнения
- Если задача создана, она автоматически отправляется на устройство
- Пользовательское сообщение связывается с созданной задачей

### Ответы агента

- Агент всегда отвечает на сообщения
- Если создана задача, ответ содержит информацию о ней
- Поддерживаются базовые диалоги (приветствие, помощь, благодарность)

## Examples

### Простой диалог без задач

```bash
curl -X POST /v1/agent/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Привет! Как дела?"
  }'
```

### Создание задачи

```bash
curl -X POST /v1/agent/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Сделай скриншот экрана",
    "device_id": "device-uuid"
  }'
```

### Продолжение существующего чата

```bash
curl -X POST /v1/agent/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Теперь кликни на кнопку",
    "session_id": "existing-session-uuid",
    "device_id": "device-uuid"
  }'
```

## Error Responses

### 404 Not Found

```json
{
  "detail": "Chat session not found"
}
```

```json
{
  "detail": "Device not found"
}
```

### 400 Bad Request

```json
{
  "detail": "Invalid request format"
}
```

## Integration

Агент интегрируется с:

- **Chat API**: Сохраняет все сообщения в чат-сессиях
- **Tasks API**: Создает задачи для выполнения на устройствах
- **WebSocket**: Отправляет задачи на подключенные устройства
- **Audit**: Логирует все действия для безопасности

## Future Enhancements

Планируемые улучшения:

- Интеграция с GPT/Claude для более умных ответов
- Поддержка контекста и многоэтапных задач
- Обработка изображений и файлов
- Планирование задач на будущее
- Интеграция с внешними API

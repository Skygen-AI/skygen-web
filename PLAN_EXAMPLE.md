# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ИНСТРУМЕНТА ПЛАНИРОВАНИЯ

## Пример запроса от пользователя:

**Пользователь:** "Составь план изучения TypeScript с нуля"

## Ответ LLM:

Создам структурированный план изучения TypeScript, который поможет вам освоить язык от основ до продвинутых концепций:

Начнем с базовых типов, затем перейдем к интерфейсам и классам, и закончим практическими проектами. План рассчитан на 4-6 недель изучения.

[[tool: plan]]
{
  "tasks": [
    {
      "id": "1",
      "title": "Основы TypeScript",
      "description": "Изучение базовых концепций TypeScript, настройка среды разработки",
      "status": "completed",
      "priority": "high",
      "level": 0,
      "dependencies": [],
      "subtasks": [
        {
          "id": "1.1",
          "title": "Установка и настройка",
          "description": "Установить TypeScript, настроить tsconfig.json и среду разработки",
          "status": "completed",
          "priority": "high",
          "tools": ["npm", "vscode", "typescript-compiler"]
        },
        {
          "id": "1.2",
          "title": "Базовые типы",
          "description": "Изучить string, number, boolean, array, tuple, enum",
          "status": "completed",
          "priority": "high",
          "tools": ["typescript-playground"]
        },
        {
          "id": "1.3",
          "title": "Type annotations",
          "description": "Научиться аннотировать переменные, функции и возвращаемые значения",
          "status": "pending",
          "priority": "medium",
          "tools": ["typescript-compiler"]
        }
      ]
    },
    {
      "id": "2",
      "title": "Интерфейсы и типы",
      "description": "Глубокое изучение системы типов TypeScript",
      "status": "in-progress",
      "priority": "high",
      "level": 0,
      "dependencies": ["1"],
      "subtasks": [
        {
          "id": "2.1",
          "title": "Интерфейсы",
          "description": "Создание и использование интерфейсов для описания объектов",
          "status": "in-progress",
          "priority": "high",
          "tools": ["typescript-compiler"]
        },
        {
          "id": "2.2",
          "title": "Union и Intersection types",
          "description": "Работа с составными типами и пересечениями",
          "status": "pending",
          "priority": "medium",
          "tools": ["typescript-playground"]
        },
        {
          "id": "2.3",
          "title": "Generics",
          "description": "Изучение дженериков для создания переиспользуемого кода",
          "status": "pending",
          "priority": "medium",
          "tools": ["typescript-compiler"]
        }
      ]
    },
    {
      "id": "3",
      "title": "Продвинутые концепции",
      "description": "Изучение сложных возможностей TypeScript",
      "status": "need-help",
      "priority": "medium",
      "level": 1,
      "dependencies": ["2"],
      "subtasks": [
        {
          "id": "3.1",
          "title": "Utility Types",
          "description": "Изучить встроенные утилитарные типы: Partial, Required, Pick, Omit",
          "status": "pending",
          "priority": "medium",
          "tools": ["typescript-handbook"]
        },
        {
          "id": "3.2",
          "title": "Conditional Types",
          "description": "Создание условных типов и продвинутых типов",
          "status": "failed",
          "priority": "low",
          "tools": ["typescript-compiler"]
        }
      ]
    },
    {
      "id": "4",
      "title": "Практические проекты",
      "description": "Применение знаний на практике в реальных проектах",
      "status": "pending",
      "priority": "high",
      "level": 1,
      "dependencies": ["2"],
      "subtasks": [
        {
          "id": "4.1",
          "title": "REST API с Express",
          "description": "Создать типизированный REST API используя Express и TypeScript",
          "status": "pending",
          "priority": "high",
          "tools": ["express", "nodejs", "typescript"]
        },
        {
          "id": "4.2",
          "title": "React приложение",
          "description": "Построить React приложение с TypeScript",
          "status": "pending",
          "priority": "medium",
          "tools": ["react", "typescript", "create-react-app"]
        }
      ]
    }
  ]
}
[[/tool: plan]]

---

## Результат в UI:

После этого ответа пользователь увидит:

1. **Текстовый ответ** с объяснением плана
2. **Интерактивный компонент планирования** с:
   - ✅ Иерархической структурой задач
   - ✅ Статусами и приоритетами
   - ✅ Зависимостями между задачами
   - ✅ Подзадачами с инструментами
   - ✅ Возможностью сворачивать/разворачивать
   - ✅ Анимированными переходами

## Альтернативный текстовый формат:

Для простых планов можно использовать текстовый формат:

```
[[tool: plan]]
1. Основы TypeScript
   Описание: Изучение базовых концепций
   Статус: pending
   Приоритет: high
   - 1.1 Установка и настройка
   - 1.2 Базовые типы
   - 1.3 Type annotations

2. Интерфейсы и типы (зависит от: 1)
   Описание: Система типов TypeScript
   - 2.1 Интерфейсы
   - 2.2 Union types
[[/tool: plan]]
```

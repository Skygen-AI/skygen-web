# 🔧 Development Mode Guide

## Что это?

Dev Mode позволяет разрабатывать UI без необходимости запуска Python бэкенда. Все API вызовы заменяются на mock-данные.

## Как включить?

### 1. Создайте файл `.env.local` в корне проекта:

```bash
# Development Mode Configuration
NEXT_PUBLIC_DEV_MODE=true

# Dev Mode Auto-Login (optional)
NEXT_PUBLIC_DEV_USER=dev@skygen.local
NEXT_PUBLIC_DEV_PASSWORD=dev123
```

### 2. Запустите приложение:

```bash
npm run dev
```

Готово! 🎉

## Что работает в Dev Mode?

✅ **Автоматическая авторизация**
- При открытии `/login` или `/register` автоматически логинит пользователя
- Никаких паролей не требуется

✅ **Mock Chat Service**
- Все чаты и сообщения работают с mock-данными
- AI отвечает заготовленными сообщениями
- Полная имитация реального функционала

✅ **Mock Auth Service**
- Регистрация и логин работают без бэкенда
- Токены сохраняются в localStorage
- Проверка авторизации работает нормально

✅ **UI Development**
- Полный доступ ко всем страницам
- Все компоненты работают
- Можно тестировать дизайн и UX

## Что НЕ работает в Dev Mode?

❌ Реальные AI ответы от агента  
❌ Скриншоты и desktop automation  
❌ WebSocket соединения  
❌ Сохранение данных на сервере  
❌ Реальная обработка задач  

## Production Mode

В продакшене Dev Mode **автоматически отключается**:

### Вариант 1: Удалите `.env.local`
```bash
rm .env.local
```

### Вариант 2: Измените значение
```bash
# .env.local
NEXT_PUBLIC_DEV_MODE=false
```

### Вариант 3: Не создавайте `.env.local` вообще
По умолчанию используется production режим

## Безопасность

🔒 **Dev Mode безопасен для продакшена:**

- Проверка использует строгое сравнение `=== 'true'`
- Любое другое значение = PROD режим
- Если переменная не установлена = PROD режим
- Mock сервисы импортируются только в dev режиме
- В продакшене используются только реальные сервисы

## Логирование

При запуске в консоли браузера вы увидите:

```
[AuthService] Mode: 🔧 DEV (Mock)
[ChatService] Mode: 🔧 DEV (Mock)
[DEV MODE] Auto-login enabled
```

В production режиме:

```
[AuthService] Mode: 🚀 PRODUCTION (Real Backend)
[ChatService] Mode: 🚀 PRODUCTION (Real Backend)
```

## Файлы и структура

```
src/services/
├── authService.ts        # Реальный сервис
├── authService.mock.ts   # Mock для dev
├── chatService.ts        # Реальный сервис
├── chatService.mock.ts   # Mock для dev
└── ...

.env.local               # Dev настройки (не в git)
.env.example            # Пример для команды
```

## Troubleshooting

### Dev Mode не работает?

1. **Проверьте `.env.local`:**
   ```bash
   cat .env.local
   ```
   Должно быть: `NEXT_PUBLIC_DEV_MODE=true`

2. **Перезапустите dev сервер:**
   ```bash
   npm run dev
   ```
   Next.js кэширует переменные окружения

3. **Проверьте консоль браузера:**
   Должны быть логи `[DEV MODE]`

### Вижу ошибки авторизации?

В dev-режиме все авторизации успешны. Если видите ошибки:
- Убедитесь что `NEXT_PUBLIC_DEV_MODE=true`
- Проверьте консоль на наличие ошибок импорта

### Хочу использовать реальный бэкенд?

Просто отключите dev режим:
```bash
# .env.local
NEXT_PUBLIC_DEV_MODE=false
```

## Рекомендации

### Для UI разработки
✅ Используйте Dev Mode  
✅ Быстрая итерация без бэкенда  
✅ Тестируйте компоненты и стили  

### Для backend интеграции
❌ Отключите Dev Mode  
✅ Запустите Python бэкенд  
✅ Тестируйте реальные API  

### Для production
❌ **Обязательно** отключите Dev Mode  
✅ Используйте реальные сервисы  
✅ Проверьте что `.env.local` не в git  

---

**Важно:** Файл `.env.local` не должен попадать в git. Он уже в `.gitignore`.



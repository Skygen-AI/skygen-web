# Skygen - Tauri Desktop App

## 🚀 Быстрый старт

### Требования
- Node.js 18+
- Rust (установлен ✅)
- npm или yarn

### Установка зависимостей
```bash
npm install
```

### Разработка

#### Запуск в режиме разработки (Tauri)
```bash
npm run tauri:dev
```
Это запустит:
1. Next.js dev server на localhost:3000
2. Tauri приложение, которое отобразит сайт

#### Запуск только веб-версии
```bash
npm run dev
```

### Сборка

#### Сборка для production
```bash
npm run tauri:build
```
Создаст установочные файлы в `src-tauri/target/release/bundle/`

#### Сборка только веб-версии
```bash
npm run build
```

## 📱 Особенности Tauri версии

- **Размер**: ~10MB (вместо 150MB+ у Electron)
- **Производительность**: Нативная скорость
- **Безопасность**: Rust backend
- **Платформы**: Windows, macOS, Linux

## 🛠 Структура проекта

```
skygen-ui/
├── src/                 # Next.js приложение
├── src-tauri/          # Tauri backend (Rust)
│   ├── src/            # Rust код
│   ├── icons/          # Иконки приложения
│   └── tauri.conf.json # Конфигурация
└── out/                # Собранные статические файлы
```

## 🔧 Конфигурация

- **Next.js**: `next.config.ts` - настроен для static export
- **Tauri**: `src-tauri/tauri.conf.json` - конфигурация приложения
- **ESLint**: Настроен для сборки production

## 🎯 Команды

| Команда | Описание |
|---------|----------|
| `npm run tauri:dev` | Запуск в режиме разработки |
| `npm run tauri:build` | Сборка для production |
| `npm run tauri` | Прямой доступ к Tauri CLI |

## ⚡ Следующие шаги

1. Протестировать: `npm run tauri:dev`
2. Настроить иконки в `src-tauri/icons/`
3. Добавить нативные функции при необходимости
4. Собрать для распространения: `npm run tauri:build`



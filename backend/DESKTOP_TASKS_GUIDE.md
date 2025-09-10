# 🖥️ Desktop Tasks Guide

## Обзор

Теперь coact_client поддерживает **Embedded Desktop Environment** - прямую автоматизацию рабочего стола без виртуальных машин!

## 🚀 Возможности

### ✅ Что работает:

- **Скриншоты** - захват экрана в реальном времени
- **Системная информация** - платформа, размер экрана, позиция курсора
- **Accessibility Tree** - XML структура доступности интерфейса
- **Выполнение команд** - shell команды и Python код
- **Набор текста** - автоматический ввод текста
- **Открытие приложений** - запуск файлов и программ
- **Активация окон** - переключение между окнами
- **Комплексные задачи** - многошаговые автоматизированные процессы

### 🎯 Доступные действия:

- `embedded_desktop_init` - инициализация
- `embedded_desktop_screenshot` - скриншоты
- `embedded_desktop_a11y` - accessibility tree
- `embedded_desktop_type` - набор текста
- `embedded_desktop_command` - выполнение команд
- `embedded_desktop_python` - Python код
- `embedded_desktop_open` - открытие файлов/приложений
- `embedded_desktop_activate` - активация окон
- `embedded_desktop_info` - информация о системе
- `embedded_desktop_action` - общие действия
- `embedded_desktop_task` - комплексные задачи
- `embedded_desktop_terminal` - вывод терминала

## 🖥️ Использование через GUI

### 1. Запуск GUI

```bash
source venv/bin/activate
python test_desktop_gui.py
```

### 2. Настройка

1. **Login** - войдите с тестовыми данными (`test@test.com` / `test@test.com`)
2. **Enroll Device** - зарегистрируйте устройство
3. **Start Client** - запустите клиент

### 3. Desktop Tasks Tab

Перейдите на вкладку **"Desktop Tasks"**:

#### Quick Actions (Быстрые действия):

- 📸 **Screenshot** - сделать скриншот
- ℹ️ **System Info** - получить информацию о системе
- 🌳 **Accessibility Tree** - получить дерево доступности
- 💻 **Terminal Output** - получить вывод терминала

#### Custom Tasks (Пользовательские задачи):

1. Выберите тип задачи из выпадающего списка
2. Отредактируйте параметры в JSON формате
3. Нажмите **"🚀 Send Task"**

#### Complex Tasks (Комплексные задачи):

- 📊 **System Analysis** - анализ системы (скриншот + команды + Python)
- 🖼️ **Screenshot + Info** - скриншот + информация о системе
- 💻 **Terminal Check** - проверка терминала

## 🔧 Использование через API

### 1. Отправка задач через API

```bash
source venv/bin/activate
python quick_test_desktop.py
```

### 2. Примеры задач

#### Простой скриншот:

```json
{
  "action": "embedded_desktop_screenshot",
  "parameters": {
    "include_base64": false
  }
}
```

#### Выполнение команды:

```json
{
  "action": "embedded_desktop_command",
  "parameters": {
    "command": "echo 'Hello from desktop automation!'",
    "shell": true
  }
}
```

#### Python код:

```json
{
  "action": "embedded_desktop_python",
  "parameters": {
    "code": "import platform; print(f'Platform: {platform.system()}')"
  }
}
```

#### Комплексная задача:

```json
{
  "action": "embedded_desktop_task",
  "parameters": {
    "actions": [
      { "type": "screenshot", "delay": 1 },
      { "type": "command", "command": "date", "shell": true, "delay": 1 },
      {
        "type": "python",
        "code": "import os; print(f'Current dir: {os.getcwd()}')",
        "delay": 1
      }
    ]
  }
}
```

## ⚡ Преимущества Embedded Desktop

### vs VM-based desktop_env:

- ✅ **Без VM overhead** - работает быстрее
- ✅ **Не нужно настраивать виртуальные машины**
- ✅ **Прямой доступ к текущей системе**
- ✅ **Меньше потребление ресурсов**
- ✅ **Проще в использовании для локальной автоматизации**

### ⚠️ Важные замечания:

- Действия выполняются на **РЕАЛЬНОЙ системе**
- Будьте осторожны с автоматизацией
- Рекомендуется тестировать в безопасной среде
- Может влиять на текущий рабочий процесс

## 🛠️ Технические детали

### Зависимости:

- `pyobjc-framework-ApplicationServices` (macOS)
- `pyobjc-framework-Quartz` (macOS)
- `pyobjc-framework-Cocoa` (macOS)
- `pyautogui` - автоматизация GUI
- `pyperclip` - работа с буфером обмена
- `lxml` - XML обработка

### Архитектура:

- **EmbeddedDesktopEnv** - основной класс для автоматизации
- **OSAdapter** - абстрактный интерфейс для OS-специфичных операций
- **MacOSAdapter** - реализация для macOS
- **Action Runner** - выполнение действий (клики, нажатия клавиш)

## 🎯 Следующие шаги

1. **Используйте embedded*desktop*\* действия** для автоматизации
2. **Интегрируйте с WebSocket API** coact_client
3. **Создавайте комплексные задачи** автоматизации
4. **Экспериментируйте с различными типами задач**

---

**🎉 Desktop automation готов к использованию!**

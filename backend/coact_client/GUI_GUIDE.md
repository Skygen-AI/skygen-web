# 🖥️ Coact Client GUI Guide

## 🎯 Обзор

Графический интерфейс Coact Client предоставляет удобный способ управления desktop agent'ом через современный GUI интерфейс, созданный на tkinter с профессиональным дизайном.

## 🚀 Запуск GUI

### Установка GUI зависимостей
```bash
# Установка с поддержкой GUI
pip install -e ".[gui]"

# Или установка всех зависимостей
pip install -e ".[all]"

# Для system tray функциональности
pip install pystray pillow
```

### Запуск приложения

```bash
# Запуск полного GUI приложения
coact-gui

# Или через Python модуль
python -m coact_client.gui_main

# Запуск только system tray (без главного окна)
coact-gui --tray-only

# Отключение system tray
coact-gui --no-tray

# Режим отладки
coact-gui --debug
```

## 🖼️ Интерфейс

### 📊 Главное Окно

#### Status Bar (Строка Состояния)
- **Authentication**: Статус аутентификации (✅/❌)
- **Device**: Статус регистрации устройства (✅/❌)  
- **Connection**: Статус WebSocket соединения (✅/❌)
- **Active Tasks**: Количество активных задач

#### Control Buttons (Кнопки Управления)
- **Login** - Вход в аккаунт
- **Enroll Device** - Регистрация устройства
- **Start Client** - Запуск клиента
- **Stop Client** - Остановка клиента
- **Refresh Status** - Обновление статуса

### 📑 Вкладки

#### 1. Dashboard (Панель управления)
- Основные элементы управления
- Статус системы в реальном времени
- Лог действий пользователя

#### 2. Logs (Журналы)
- Журналы приложения в реальном времени
- Фильтрация по уровням логирования
- Возможность сохранения логов
- Auto-scroll функция

#### 3. Tasks (Задачи)
- История выполненных задач
- Информация о статусе задач
- Количество действий в каждой задаче
- Временные метки

#### 4. Settings (Настройки)
- Просмотр текущей конфигурации
- Информация о путях и директориях
- Параметры безопасности
- Настройки сервера

### 🔐 Диалог Входа

#### Функции Login Dialog
- **Professional Design**: Современный дизайн интерфейса
- **Email/Password**: Стандартная аутентификация  
- **Remember Credentials**: Опция сохранения данных
- **Progress Indicator**: Индикатор процесса входа
- **Error Handling**: Обработка ошибок входа
- **Signup Link**: Ссылка на регистрацию

#### Использование
1. Нажмите кнопку "Login" в главном окне
2. Введите email и пароль
3. Отметьте "Remember credentials" для сохранения
4. Нажмите "Login" для входа

## 🔧 System Tray

### Функции System Tray
- **Smart Icon**: Иконка меняется в зависимости от статуса подключения
- **Context Menu**: Контекстное меню с основными функциями
- **Notifications**: Системные уведомления
- **Quick Actions**: Быстрый доступ к основным функциям

### Меню System Tray
- **Show Coact Client** - Показать главное окно
- **Status** - Показать статус системы
- **Connect/Disconnect** - Управление соединением
- **Login/Logout** - Управление аутентификацией
- **Settings** - Настройки (переход к GUI)
- **About** - Информация о приложении
- **Exit** - Выход из приложения

### Индикаторы
- 🟢 **Зеленая иконка** - Подключен и активен
- ⚫ **Серая иконка** - Отключен или неактивен
- **Tooltip** - Показывает текущий статус при наведении

## 🎨 Дизайн и Стили

### Цветовая Схема
- **Primary**: #2196F3 (Синий)
- **Success**: #4CAF50 (Зеленый)  
- **Warning**: #FF9800 (Оранжевый)
- **Error**: #F44336 (Красный)
- **Background**: #f0f0f0 (Светло-серый)

### Компоненты
- **Card Frames**: Белые рамки с тенями
- **Status Indicators**: Цветные индикаторы состояния
- **Professional Buttons**: Кнопки в фирменном стиле
- **Tabbed Interface**: Организованные вкладки

## 🔄 Жизненный Цикл GUI

### Инициализация
1. Загрузка конфигурации
2. Настройка стилей и тем
3. Создание основного окна
4. Инициализация system tray
5. Запуск async event loop

### Обновления Статуса
- **Автоматическое обновление** каждые 5 секунд
- **Обновление по требованию** через кнопку Refresh
- **Реактивные обновления** на события

### Закрытие
1. Подтверждение выхода
2. Остановка фоновых задач
3. Закрытие async loop
4. Очистка system tray
5. Корректное завершение

## 🛠️ Разработка GUI

### Архитектура
```
gui/
├── __init__.py              # GUI пакет
├── main_window.py           # Главное окно
├── login_dialog.py          # Диалог входа
├── system_tray.py           # System tray
└── gui_main.py              # Точка входа
```

### Основные Классы
- **CoactGUI** - Главное приложение
- **LoginDialog** - Диалог аутентификации
- **SystemTray** - System tray интеграция

### Threading Model
- **Main Thread** - GUI и tkinter
- **Async Thread** - Coact backend операции
- **Background Threads** - System tray и периодические задачи

### Event Handling
- **GUI Events** - Обработка через tkinter callbacks
- **Async Events** - Через asyncio.run_coroutine_threadsafe()
- **System Events** - Через system tray callbacks

## 🔧 Кастомизация

### Темы и Стили
```python
# Настройка стилей в main_window.py
self.style.configure("Accent.TButton",
                   background="#2196F3",
                   foreground="white")
```

### Иконки
```python
# Создание custom иконки в system_tray.py  
def create_icon_image(self, connected: bool = False) -> Image.Image:
    # Custom icon logic
    pass
```

### Расширение Функциональности
- Добавление новых вкладок в `_create_widgets()`
- Расширение context menu в `create_menu()`
- Добавление новых диалогов

## 📱 Мобильность

### Поддержка Платформ
- ✅ **Windows** - Полная поддержка + system tray
- ✅ **macOS** - Полная поддержка + menu bar
- ✅ **Linux** - Полная поддержка + system tray

### Адаптивность
- Минимальный размер окна: 800x600
- Автоматическое масштабирование элементов
- Responsive layout для разных разрешений

## ⚡ Performance

### Оптимизации
- **Lazy Loading** - Загрузка данных по требованию
- **Async Updates** - Неблокирующие обновления UI
- **Efficient Rendering** - Обновление только измененных элементов
- **Resource Management** - Правильное управление памятью

### Мониторинг
- CPU usage мониторинг для GUI операций
- Memory usage tracking
- Response time измерения

## 🐛 Troubleshooting

### Общие Проблемы

#### GUI не запускается
```bash
# Проверка tkinter
python -c "import tkinter; print('tkinter OK')"

# Проверка PIL
python -c "from PIL import Image; print('PIL OK')"

# Установка недостающих пакетов
pip install pillow pystray
```

#### System Tray не работает
```bash
# Linux: установка системных зависимостей
sudo apt-get install python3-tk

# macOS: убедитесь что используете системный Python
# Windows: обычно работает из коробки
```

#### Медленная работа
- Отключите debug режим: `--no-debug`
- Уменьшите частоту обновлений в коде
- Проверьте background процессы

### Логирование
```python
# Включение debug логов для GUI
coact-gui --debug --log-level DEBUG
```

## 🚀 Advanced Usage

### Программное Управление
```python
from coact_client.gui.main_window import CoactGUI

# Создание GUI программно
gui = CoactGUI()
gui.run()
```

### Интеграция с CLI
```python
# Запуск GUI из CLI кода
from coact_client.gui_main import main as gui_main
gui_main()
```

### Custom Plugins
```python
# Расширение GUI собственными модулями
class CustomDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        # Custom dialog logic
```

---

**🎯 GUI готов к production использованию!** 

Полнофункциональный графический интерфейс с:
- ✅ Professional дизайн
- ✅ System tray интеграция  
- ✅ Real-time мониторинг
- ✅ Intuitive user experience
- ✅ Cross-platform поддержка

Используйте `coact-gui` для запуска! 🚀
# Интеграция coact_client с desktop_env

Этот документ описывает как использовать интеграцию между coact_client и desktop_env для автоматизации управления компьютером.

## 🎯 Обзор

Интеграция позволяет coact_client использовать desktop_env как backend для выполнения сложных задач автоматизации рабочего стола через виртуальные машины и контейнеры.

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Установите desktop_env
pip install desktop_env

# Установите необходимые зависимости для VM провайдеров
# Для VMware:
# - VMware Workstation/Fusion
# - pyVmomi

# Для VirtualBox:
# - VirtualBox
# - pyvbox

# Для Docker:
pip install docker

# Для облачных провайдеров:
pip install boto3 google-cloud-compute azure-mgmt-compute
```

### 2. Запуск примера

```bash
# Запустите пример интеграции
python desktop_env_integration_example.py
```

## 📋 Доступные Action Handlers

### `desktop_env_init` - Инициализация среды

Инициализирует desktop_env с указанными параметрами.

```json
{
    "type": "desktop_env_init",
    "provider_name": "vmware",
    "vm_path": "/path/to/vm.vmx",
    "headless": true,
    "action_space": "pyautogui"
}
```

### `desktop_env_reset` - Сброс среды

Сбрасывает среду в исходное состояние и настраивает задачу.

```json
{
    "type": "desktop_env_reset",
    "task_config": {
        "id": "task_001",
        "instruction": "Complete this task",
        "config": [],
        "evaluator": {"func": "infeasible"}
    }
}
```

### `desktop_env_action` - Выполнение действия

Выполняет единичное действие в среде.

```json
{
    "type": "desktop_env_action",
    "action_type": "CLICK",
    "coordinates": [100, 200],
    "button": "left"
}
```

или с pyautogui командой:

```json
{
    "type": "desktop_env_action",
    "command": "pyautogui.click(100, 200)"
}
```

### `desktop_env_screenshot` - Скриншот

Создает скриншот текущего состояния экрана.

```json
{
    "type": "desktop_env_screenshot"
}
```

### `desktop_env_a11y` - Accessibility Tree

Получает дерево доступности для анализа элементов интерфейса.

```json
{
    "type": "desktop_env_a11y"
}
```

### `desktop_env_evaluate` - Оценка задачи

Оценивает выполнение текущей задачи.

```json
{
    "type": "desktop_env_evaluate"
}
```

### `desktop_env_info` - Информация о VM

Получает информацию о виртуальной машине.

```json
{
    "type": "desktop_env_info"
}
```

### `desktop_env_task` - Комплексная задача

Выполняет комплексную задачу с несколькими шагами.

```json
{
    "type": "desktop_env_task",
    "task_config": {
        "id": "complex_task",
        "instruction": "Complete multi-step task",
        "config": [],
        "evaluator": {"func": "infeasible"}
    },
    "actions": [
        {"command": "pyautogui.click(100, 100)"},
        {"command": "pyautogui.typewrite('Hello World')"},
        {"command": "pyautogui.press('enter')"}
    ],
    "evaluate": true
}
```

## 🔧 Конфигурация провайдеров

### VMware

```python
desktop_env_module = DesktopEnvModule(
    provider_name="vmware",
    vm_path="/path/to/your/vm.vmx",
    headless=True,
    action_space="pyautogui"
)
```

### VirtualBox

```python
desktop_env_module = DesktopEnvModule(
    provider_name="virtualbox",
    vm_path="/path/to/your/vm.vbox",
    headless=True,
    action_space="pyautogui"
)
```

### Docker

```python
desktop_env_module = DesktopEnvModule(
    provider_name="docker",
    vm_path="ubuntu:desktop-env",  # Docker image name
    headless=True,
    action_space="pyautogui"
)
```

### AWS

```python
desktop_env_module = DesktopEnvModule(
    provider_name="aws",
    vm_path="ami-12345678",  # AMI ID
    headless=True,
    action_space="pyautogui"
)
```

## 🎮 Action Spaces

### pyautogui (рекомендуется)

Использует pyautogui команды для управления:
- `pyautogui.click(x, y)`
- `pyautogui.typewrite('text')`
- `pyautogui.press('key')`
- `pyautogui.scroll(clicks)`

### computer_13

Использует структурированные действия:
- `{"action_type": "CLICK", "coordinates": [x, y]}`
- `{"action_type": "TYPE", "text": "hello"}`
- `{"action_type": "KEY", "key": "enter"}`

### claude_computer_use

Совместимость с Claude Computer Use API.

## 📝 Примеры использования

### Простой клик

```python
from coact_client.modules.desktop_env import desktop_env_module

# Инициализация
await desktop_env_module.initialize()

# Выполнение клика
result = await desktop_env_module.execute_action({
    "type": "CLICK",
    "coordinates": [100, 100]
})

print(result)
```

### Комплексная задача

```python
task_result = await desktop_env_module.execute_complex_task({
    "task_config": {
        "id": "text_editor_task",
        "instruction": "Open text editor and write a message",
        "evaluator": {"func": "infeasible"}
    },
    "actions": [
        {"command": "pyautogui.hotkey('cmd', 'space')"},  # Spotlight
        {"command": "pyautogui.typewrite('TextEdit')"},
        {"command": "pyautogui.press('enter')"},
        {"command": "pyautogui.typewrite('Hello from automation!')"}
    ],
    "evaluate": True
})
```

### Мониторинг и скриншоты

```python
# Создание скриншота
screenshot = await desktop_env_module.take_screenshot({})

# Получение accessibility tree
a11y_tree = await desktop_env_module.get_accessibility_tree({})

# Информация о VM
vm_info = await desktop_env_module.get_vm_info({})
```

## 🛠️ Настройка VM

### Подготовка Ubuntu VM для desktop_env

1. Установите Ubuntu Desktop в VM
2. Настройте автологин
3. Установите необходимые пакеты:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip
   sudo apt install -y xvfb x11vnc fluxbox
   ```

4. Создайте snapshot "init_state"

### Настройка сети

Убедитесь, что VM имеет сетевое соединение для связи с coact_client.

## 🚨 Устранение неисправностей

### Ошибка "desktop_env library not available"

```bash
pip install desktop_env
```

### Ошибка подключения к VM

1. Проверьте, что VM запущена
2. Проверьте сетевые настройки
3. Убедитесь в правильности путей к VM

### Проблемы с действиями GUI

1. Убедитесь, что GUI доступен в VM
2. Проверьте разрешение экрана
3. Попробуйте без headless режима для отладки

### Низкая производительность

1. Выделите больше ресурсов VM (CPU, RAM)
2. Используйте локальные провайдеры вместо облачных
3. Оптимизируйте действия (уменьшите pause между командами)

## 📊 Мониторинг и логи

Все действия логируются через стандартный Python logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coact_client.modules.desktop_env")
```

## 🔒 Безопасность

1. Используйте изолированные VM для выполнения задач
2. Регулярно создавайте snapshots для восстановления
3. Ограничьте сетевой доступ VM при необходимости
4. Мониторьте выполняемые команды

## 🤝 Интеграция с coact_client

Модуль автоматически регистрируется при запуске coact_client и доступен через WebSocket API и task engine.

Все action handlers автоматически регистрируются в `coact_client.app` и доступны для выполнения через WebSocket подключения.

## 📚 Дополнительная документация

- [desktop_env GitHub](https://github.com/xlang-ai/desktop_env)
- [coact_client документация](./PROJECT_OVERVIEW.md)
- [Примеры задач](./test_task.py)

## 🎯 Roadmap

- [ ] Поддержка большего количества action spaces
- [ ] Интеграция с облачными провайдерами
- [ ] Улучшенная обработка ошибок
- [ ] Поддержка параллельных VM
- [ ] Интеграция с AI агентами для автоматического планирования задач
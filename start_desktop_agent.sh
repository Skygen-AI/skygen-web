#!/bin/bash

# Скрипт для запуска desktop_env агента
# Использование: ./start_desktop_agent.sh

echo "🤖 Запуск Desktop Environment Agent..."

# Переходим в правильную директорию
cd "$(dirname "$0")/backend/backend"

# Активируем виртуальное окружение
echo "📦 Активация виртуального окружения..."
source venv/bin/activate

# Запускаем агент
echo "🚀 Запуск агента..."
python ../simple_desktop_agent.py

# Если агент остановился, показываем сообщение
echo "🛑 Desktop agent остановлен"

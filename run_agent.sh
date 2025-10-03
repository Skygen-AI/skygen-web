#!/bin/bash

# 🤖 Desktop Environment Agent Runner
# Автоматический запуск и перезапуск desktop_env агента

COLOR_GREEN='\033[0;32m'
COLOR_BLUE='\033[0;34m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_NC='\033[0m' # No Color

# Функция для вывода цветного текста
print_status() {
    echo -e "${COLOR_BLUE}[$(date '+%H:%M:%S')]${COLOR_NC} $1"
}

print_success() {
    echo -e "${COLOR_GREEN}✅ $1${COLOR_NC}"
}

print_warning() {
    echo -e "${COLOR_YELLOW}⚠️  $1${COLOR_NC}"
}

print_error() {
    echo -e "${COLOR_RED}❌ $1${COLOR_NC}"
}

# Проверяем что находимся в правильной директории
if [ ! -d "backend/backend" ]; then
    print_error "Запускайте скрипт из корня проекта skygen-web"
    exit 1
fi

print_status "🚀 Запуск Desktop Environment Agent..."

# Переходим в backend директорию
cd backend/backend

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    print_error "Виртуальное окружение не найдено в backend/backend/venv"
    print_warning "Создайте его командой: python -m venv venv"
    exit 1
fi

# Активируем виртуальное окружение
print_status "📦 Активация виртуального окружения..."
source venv/bin/activate

# Проверяем наличие необходимых пакетов
print_status "🔍 Проверка зависимостей..."
python -c "import websockets" 2>/dev/null || {
    print_error "Пакет websockets не установлен"
    print_warning "Установите: pip install websockets"
    exit 1
}

# Проверяем наличие файла агента
if [ ! -f "../simple_desktop_agent.py" ]; then
    print_error "Файл simple_desktop_agent.py не найден"
    exit 1
fi

# Функция для обработки остановки
cleanup() {
    print_warning "Получен сигнал остановки..."
    print_status "🛑 Завершение работы агента..."
    exit 0
}

# Обработка Ctrl+C
trap cleanup SIGINT SIGTERM

print_success "Все проверки пройдены!"
print_status "🤖 Запуск Desktop Agent..."
echo
print_status "💡 Для остановки нажмите Ctrl+C"
echo
print_status "📋 Лог активности:"
echo "----------------------------------------"

# Запуск с автоматическим перезапуском
while true; do
    print_status "▶️  Запуск агента..."
    
    # Запускаем агент
    python ../simple_desktop_agent.py
    
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_warning "Агент завершил работу нормально"
        break
    else
        print_error "Агент завершил работу с ошибкой (код: $exit_code)"
        print_status "🔄 Перезапуск через 5 секунд..."
        sleep 5
    fi
done

print_status "👋 Desktop Agent остановлен"

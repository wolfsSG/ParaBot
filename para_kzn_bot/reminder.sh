#!/bin/bash

# Пути
VENV_PATH="/home/orangepi/parabot_venv/bin/activate"
PROJECT_DIR="/home/orangepi/ParaBot/para_kzn_bot/bot"

# Лог-файл
LOG_FILE="/home/orangepi/ParaBot/para_kzn_bot/bot/reminder.log"

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Проверяем существование виртуального окружения
if [ ! -f "$VENV_PATH" ]; then
    log "ERROR: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Активируем окружение
source "$VENV_PATH" || {
    log "ERROR: Failed to activate virtual environment"
    exit 1
}

# Проверяем существование директории проекта
if [ ! -d "$PROJECT_DIR" ]; then
    log "ERROR: Project directory not found at $PROJECT_DIR"
    exit 1
fi

# Переходим в директорию проекта
cd "$PROJECT_DIR" || {
    log "ERROR: Failed to change to project directory"
    exit 1
}

# Небольшая задержка перед запуском
sleep 2

# Запускаем скрипт и логируем результат
log "Starting reminder script"
python reminder.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "Reminder script completed successfully"
else
    log "ERROR: Reminder script failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
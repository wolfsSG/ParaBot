#!/bin/bash

# Пути
VENV_PATH="/home/user/parabot_venv/bin/activate"
PROJECT_DIR="/home/user/ParaBot/para_kzn_bot/bot"

# Активируем окружение
source "$VENV_PATH" || {
    exit 1
}

# Ждем инициализации
sleep 5

# Переходим и запускаем
cd "$PROJECT_DIR" || {
    exit 1
}

python reminder.py

exit $?

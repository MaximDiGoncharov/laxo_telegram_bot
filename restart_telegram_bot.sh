#!/bin/bash

PROCESS_NAME="bot.py"

# Проверка, запущен ли процесс
if pgrep -f "$PROCESS_NAME" > /dev/null; then
    echo "$PROCESS_NAME уже запущен."
else
    nohup python3 /home/maxim/repos/telegram/bot.py > output.log 2>&1 &
fi

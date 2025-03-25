запустить виртуально окружение выполнив команду, в директории проекта
python -m venv .


Запуск скрипта
nohup python bot.py > output.log 2>&1 &


Мониторинг бота
скрипт restart_telegram_bot.sh 
Запущен на cron, каждые 5 минут 
Проверить crontab -l
Создать crontaab -e 

#!/bin/bash

# Путь к лог-файлу
LOG_FILE="update_map.log"

# Загружаем переменные из .env
if [ -f .env ]; then
    source .env
else
    echo "Ошибка: файл .env не найден"
    exit 1
fi

# Функция для логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Начало выполнения
log "Начало обновления карты"

# Переходим в директорию скрипта
cd "$(dirname "$0")"

# Запускаем Python скрипты
log "Запуск main.py"
python3 main.py
if [ $? -ne 0 ]; then
    log "Ошибка при выполнении main.py"
    exit 1
fi

log "Запуск gen_tg_cheb_map.py"
python3 gen_tg_cheb_map.py
if [ $? -ne 0 ]; then
    log "Ошибка при выполнении gen_tg_cheb_map.py"
    exit 1
fi

# Копируем файлы на удаленный сервер через FTP
log "Копирование файлов на сервер"

# Выполняем FTP команды
ftp -p -n "$SERVER_HOST" << EOF | tee -a "$LOG_FILE"
quote USER $SERVER_USER
quote PASS $SERVER_PASSWORD
cd wordpress_14/public_html/mapcheb
binary
put data/map.html index.html
put telegram_channels.db telegram_channels.db
bye
EOF

if [ $? -ne 0 ]; then
    log "Ошибка при копировании файлов на сервер"
    exit 1
fi

log "Обновление карты успешно завершено" 
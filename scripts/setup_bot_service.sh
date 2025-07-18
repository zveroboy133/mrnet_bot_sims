#!/bin/bash

# Скрипт для настройки systemd сервиса для бота

SERVICE_NAME="pachka-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔧 Настройка systemd сервиса для бота Pachka..."

# Проверяем права root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
    exit 1
fi

# Копируем файл сервиса
echo "📋 Копируем файл сервиса..."
cp "${SCRIPT_DIR}/pachka-bot.service" "$SERVICE_FILE"

# Обновляем пути в файле сервиса
echo "🔧 Обновляем пути в файле сервиса..."
sed -i "s|/c%3A/devs/find_sims-main|${SCRIPT_DIR}|g" "$SERVICE_FILE"

# Перезагружаем systemd
echo "🔄 Перезагружаем systemd..."
systemctl daemon-reload

# Включаем автозапуск
echo "✅ Включаем автозапуск сервиса..."
systemctl enable "$SERVICE_NAME"

echo "🎉 Сервис настроен!"
echo ""
echo "📋 Команды для управления:"
echo "   Запуск:     sudo systemctl start $SERVICE_NAME"
echo "   Остановка:  sudo systemctl stop $SERVICE_NAME"
echo "   Перезапуск: sudo systemctl restart $SERVICE_NAME"
echo "   Статус:     sudo systemctl status $SERVICE_NAME"
echo "   Логи:       sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "🚀 Для запуска бота выполните: sudo systemctl start $SERVICE_NAME" 
#!/bin/bash

# Скрипт для проверки статуса бота

BOT_PID_FILE="bot.pid"
SERVICE_NAME="pachka-bot"

echo "🔍 Проверка статуса бота Pachka..."
echo ""

# Проверяем systemd сервис
echo "📋 Systemd сервис:"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Сервис $SERVICE_NAME активен"
    systemctl status "$SERVICE_NAME" --no-pager -l
else
    echo "❌ Сервис $SERVICE_NAME неактивен"
fi

echo ""

# Проверяем PID файл
echo "📋 PID файл:"
if [ -f "$BOT_PID_FILE" ]; then
    PID=$(cat "$BOT_PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Процесс с PID $PID запущен"
        ps aux | grep $PID | grep -v grep
    else
        echo "❌ Процесс с PID $PID не найден (старый PID файл)"
    fi
else
    echo "ℹ️ PID файл не найден"
fi

echo ""

# Проверяем порт
echo "🌐 Проверка порта 5000:"
if netstat -tlnp 2>/dev/null | grep :5000 > /dev/null; then
    echo "✅ Порт 5000 открыт"
    netstat -tlnp 2>/dev/null | grep :5000
else
    echo "❌ Порт 5000 не открыт"
fi

echo ""

# Проверяем health endpoint
echo "🏥 Проверка health endpoint:"
if curl -s http://91.217.77.71:5000/health > /dev/null; then
    echo "✅ Health endpoint доступен"
    curl -s http://91.217.77.71:5000/health | jq . 2>/dev/null || curl -s http://91.217.77.71:5000/health
else
    echo "❌ Health endpoint недоступен"
fi

echo ""

# Показываем последние логи
echo "📊 Последние логи (последние 10 строк):"
if [ -f "bot.log" ]; then
    tail -10 bot.log
else
    echo "ℹ️ Файл логов не найден"
fi 
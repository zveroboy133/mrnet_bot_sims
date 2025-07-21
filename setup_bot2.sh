#!/bin/bash

echo "🤖 Установка второго бота Pachka..."

# Проверяем наличие конфигурационного файла
if [ ! -f "bots_config.json" ]; then
    echo "❌ Файл bots_config.json не найден!"
    exit 1
fi

# Проверяем наличие универсального бота
if [ ! -f "llms_bot_pachka/universal_bot.py" ]; then
    echo "❌ Файл llms_bot_pachka/universal_bot.py не найден!"
    exit 1
fi

# Копируем systemd сервис
echo "📋 Копируем systemd сервис..."
sudo cp pachka-bot-2.service /etc/systemd/system/

# Перезагружаем systemd
echo "🔄 Перезагружаем systemd..."
sudo systemctl daemon-reload

# Включаем автозапуск
echo "✅ Включаем автозапуск..."
sudo systemctl enable pachka-bot-2

echo "🎉 Второй бот установлен!"
echo ""
echo "📋 Команды для управления:"
echo "  Запуск: sudo systemctl start pachka-bot-2"
echo "  Остановка: sudo systemctl stop pachka-bot-2"
echo "  Перезапуск: sudo systemctl restart pachka-bot-2"
echo "  Статус: sudo systemctl status pachka-bot-2"
echo "  Логи: sudo journalctl -u pachka-bot-2 -f"
echo ""
echo "🚀 Запускаем второго бота..."
sudo systemctl start pachka-bot-2

echo "✅ Готово! Второй бот запущен на порту 5001" 
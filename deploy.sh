#!/bin/bash

# Скрипт для быстрого обновления приложения на сервере

echo "🚀 Начинаем обновление приложения..."

# Проверяем, какой Docker Compose доступен
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo "✅ Используем docker-compose (старая версия)"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo "✅ Используем docker compose (новая версия)"
else
    echo "❌ Docker Compose не найден!"
    echo "📦 Установите Docker Compose:"
    echo "   sudo apt update && sudo apt install docker-compose"
    echo "   или"
    echo "   sudo curl -L 'https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)' -o /usr/local/bin/docker-compose"
    echo "   sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "📦 Установите Docker:"
    echo "   sudo apt update && sudo apt install docker.io"
    echo "   sudo systemctl start docker"
    echo "   sudo systemctl enable docker"
    exit 1
fi

# Остановка существующего контейнера
echo "⏹️ Останавливаем существующий контейнер..."
$DOCKER_COMPOSE down 2>/dev/null || echo "ℹ️ Контейнер не был запущен"

# Удаление старого образа (опционально, для экономии места)
echo "🗑️ Удаляем старый образ..."
docker rmi find-sims-main_find-sims-app 2>/dev/null || true

# Сборка нового образа
echo "🔨 Собираем новый образ..."
$DOCKER_COMPOSE build --no-cache

# Запуск нового контейнера
echo "▶️ Запускаем новый контейнер..."
$DOCKER_COMPOSE up -d

# Проверка статуса
echo "✅ Проверяем статус..."
$DOCKER_COMPOSE ps

echo "🎉 Обновление завершено!"
echo "📊 Логи: $DOCKER_COMPOSE logs -f"
echo "🛑 Остановка: $DOCKER_COMPOSE down" 
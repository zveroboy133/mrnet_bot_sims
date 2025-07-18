#!/bin/bash

echo "🚀 Универсальный скрипт развертывания"

# Проверяем доступные компоненты
echo "🔍 Проверяем доступные компоненты..."

DOCKER_AVAILABLE=false
VENV_AVAILABLE=false

# Проверяем Docker
if command -v docker &> /dev/null; then
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        DOCKER_AVAILABLE=true
        echo "✅ Docker и Docker Compose доступны"
    else
        echo "⚠️ Docker доступен, но Docker Compose отсутствует"
    fi
else
    echo "❌ Docker не установлен"
fi

# Проверяем Python
if command -v python3 &> /dev/null; then
    VENV_AVAILABLE=true
    echo "✅ Python3 доступен"
else
    echo "❌ Python3 не установлен"
fi

# Выбираем метод развертывания
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "🐳 Используем Docker для развертывания..."
    ./scripts/deploy.sh
elif [ "$VENV_AVAILABLE" = true ]; then
    echo "🐍 Используем виртуальное окружение для развертывания..."
    ./scripts/update_code.sh
else
    echo "❌ Нет доступных методов развертывания!"
    echo ""
    echo "📦 Установите Docker:"
    echo "   sudo ./scripts/install_docker.sh"
    echo ""
    echo "🐍 Или установите Python3:"
    echo "   sudo apt update && sudo apt install python3 python3-venv python3-pip"
    echo ""
    echo "После установки запустите этот скрипт снова."
    exit 1
fi 
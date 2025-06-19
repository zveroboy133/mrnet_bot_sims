#!/bin/bash

echo "🐳 Установка Docker и Docker Compose..."

# Проверяем, что мы root или используем sudo
if [ "$EUID" -ne 0 ]; then
    echo "🔐 Требуются права администратора. Запустите с sudo:"
    echo "   sudo ./install_docker.sh"
    exit 1
fi

# Обновляем пакеты
echo "📦 Обновляем пакеты..."
apt update

# Устанавливаем Docker
echo "🐳 Устанавливаем Docker..."
apt install -y docker.io

# Запускаем и включаем Docker
echo "▶️ Запускаем Docker..."
systemctl start docker
systemctl enable docker

# Добавляем текущего пользователя в группу docker
echo "👤 Добавляем пользователя в группу docker..."
usermod -aG docker $SUDO_USER

# Устанавливаем Docker Compose
echo "📋 Устанавливаем Docker Compose..."

# Пробуем установить через apt
if apt install -y docker-compose; then
    echo "✅ Docker Compose установлен через apt"
else
    echo "📥 Скачиваем Docker Compose с GitHub..."
    # Определяем архитектуру
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="x86_64"
    elif [ "$ARCH" = "aarch64" ]; then
        ARCH="aarch64"
    elif [ "$ARCH" = "armv7l" ]; then
        ARCH="armv7"
    fi
    
    # Скачиваем последнюю версию
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$ARCH" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    echo "✅ Docker Compose установлен с GitHub"
fi

# Проверяем установку
echo "🔍 Проверяем установку..."
docker --version
docker-compose --version 2>/dev/null || docker compose version

echo "🎉 Установка завершена!"
echo "⚠️ Перезагрузитесь или выполните: newgrp docker"
echo "🚀 Теперь можете запустить: ./deploy.sh" 
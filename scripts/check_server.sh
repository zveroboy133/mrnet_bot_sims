#!/bin/bash

echo "🔍 Проверка установленных компонентов на сервере..."

echo "📦 Python:"
python3 --version 2>/dev/null || echo "❌ Python3 не установлен"

echo "🐳 Docker:"
docker --version 2>/dev/null || echo "❌ Docker не установлен"

echo "📋 Docker Compose:"
docker-compose --version 2>/dev/null || echo "❌ Docker Compose не установлен"

echo "📋 Docker Compose (новый формат):"
docker compose version 2>/dev/null || echo "❌ Docker Compose (новый) не установлен"

echo "📚 pip:"
pip3 --version 2>/dev/null || echo "❌ pip3 не установлен"

echo "🔧 git:"
git --version 2>/dev/null || echo "❌ git не установлен"

echo "✅ Проверка завершена!" 
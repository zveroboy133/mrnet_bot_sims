#!/usr/bin/env python3
"""
Скрипт для запуска бота Pachka
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к папке с ботом
sys.path.append(os.path.join(os.path.dirname(__file__), 'llms_bot_pachka'))

def main():
    print("🤖 Запуск бота Pachka...")
    
    # Проверяем наличие токена
    token = os.getenv("PACHKA_TOKEN")
    if not token:
        print("❌ Ошибка: Не установлена переменная окружения PACHKA_TOKEN")
        print("📝 Создайте файл .env в корне проекта:")
        print("   PACHKA_TOKEN=ваш_токен_здесь")
        return
    
    print(f"✅ Токен найден: {token[:10]}...")
    
    try:
        # Импортируем и запускаем бота
        from bot import main as bot_main
        print("🚀 Запускаем бота...")
        bot_main()
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📁 Убедитесь, что файл llms_bot_pachka/bot.py существует")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main() 
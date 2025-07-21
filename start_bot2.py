#!/usr/bin/env python3
"""
Скрипт для запуска второго бота Pachka
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к папке с ботом
sys.path.append(os.path.join(os.path.dirname(__file__), 'llms_bot_pachka'))

def main():
    print("🤖 Запуск второго бота Pachka...")
    
    try:
        # Импортируем и запускаем универсальный бота
        from universal_bot import main as bot_main
        print("🚀 Запускаем второго бота...")
        
        # Устанавливаем аргумент командной строки для второго бота
        sys.argv = ['start_bot2.py', 'bot2']
        
        bot_main()
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📁 Убедитесь, что файл llms_bot_pachka/universal_bot.py существует")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Скрипт для запуска третьего бота Pachka (универсальный)
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем путь к папке с ботом
sys.path.append(os.path.join(os.path.dirname(__file__), 'llms_bot_pachka'))

def check_configuration():
    """Проверяет конфигурацию перед запуском"""
    load_dotenv()
    
    errors = []
    warnings = []
    
    # Проверяем файл .env
    if not os.path.exists(".env"):
        errors.append("Файл .env не найден. Создайте его на основе env.example")
    
    # Проверяем bots_config.json для universal_bot
    if not os.path.exists("bots_config.json"):
        errors.append("bots_config.json не найден (обязателен для universal_bot)")
        errors.append("  Скопируйте bots_config.example.json и заполните: cp bots_config.example.json bots_config.json")
    
    # Проверяем опциональные переменные
    sheets_id = os.getenv("GOOGLE_SHEETS_ID")
    if not sheets_id or sheets_id.startswith("ваш_") or sheets_id.startswith("ВАШ_"):
        warnings.append("GOOGLE_SHEETS_ID не установлена (необязательно для простого бота)")
    
    # Проверяем Google credentials (необязательно для простого бота)
    if not os.path.exists("client_secret.json"):
        warnings.append("client_secret.json не найден (необязательно для простого бота)")
    
    return errors, warnings

def print_help():
    """Выводит справку"""
    print("=" * 70)
    print("🤖 MRNet Bot SIMs - Запуск третьего бота (универсальный)")
    print("=" * 70)
    print()
    print("Использование:")
    print("  python start_bot3.py         # Запуск третьего бота (bot3)")
    print("  python start_bot3.py --check  # Проверка конфигурации")
    print("  python start_bot3.py --help   # Показать эту справку")
    print()
    print("Обязательные файлы:")
    print("  bots_config.json   - Конфигурация ботов (создайте из bots_config.example.json)")
    print("  .env               - Переменные окружения (создайте из env.example)")
    print()
    print("Токены для ботов берутся из bots_config.json:")
    print("  - webhook_incoming: URL webhook для получения сообщений")
    print("  - access_token: API токен для отправки сообщений")
    print("  - signing_secret: Секрет для подписи webhook")
    print()
    print("Для проверки конфигурации используйте:")
    print("  python check_config.py")
    print("=" * 70)
    print()

def main():
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print_help()
            return
        elif sys.argv[1] == "--check" or sys.argv[1] == "-c":
            # Запускаем проверку конфигурации
            from check_config import main as check_main
            check_main()
            return
    
    print("🤖 Запуск третьего бота Pachka (универсальный)...")
    print()
    
    # Проверяем конфигурацию
    errors, warnings = check_configuration()
    
    if errors:
        print("❌ Обнаружены ошибки конфигурации:")
        for error in errors:
            print(f"   • {error}")
        print()
        print("💡 Исправьте ошибки и попробуйте снова.")
        print("   Для подробной проверки: python check_config.py")
        print("   Для справки: python start_bot3.py --help")
        sys.exit(1)
    
    if warnings:
        print("⚠️  Предупреждения:")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    # Загружаем переменные окружения
    load_dotenv()
    
    try:
        # Импортируем и запускаем универсальный бота
        from universal_bot import main as bot_main
        print("🚀 Запускаем бота...")
        print()
        
        # Устанавливаем аргумент командной строки для третьего бота
        sys.argv = ['start_bot3.py', 'bot3']
        
        bot_main()
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📁 Убедитесь, что файл llms_bot_pachka/universal_bot.py существует")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


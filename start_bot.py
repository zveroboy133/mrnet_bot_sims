#!/usr/bin/env python3
"""
Скрипт для запуска бота Pachka
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
    
    # Проверяем обязательные переменные
    token = os.getenv("PACHKA_TOKEN")
    if not token or token.startswith("ваш_") or token.startswith("ВАШ_"):
        errors.append("PACHKA_TOKEN не установлена или содержит значение по умолчанию")
        errors.append("  Получите токен в настройках бота: Автоматизации -> Webhooks")
    
    sheets_id = os.getenv("GOOGLE_SHEETS_ID")
    if not sheets_id or sheets_id.startswith("ваш_") or sheets_id.startswith("ВАШ_"):
        errors.append("GOOGLE_SHEETS_ID не установлена или содержит значение по умолчанию")
        errors.append("  Укажите ID вашей таблицы Google Sheets")
    
    # Проверяем Google credentials
    if not os.path.exists("client_secret.json"):
        errors.append("client_secret.json не найден")
        errors.append("  Скопируйте client_secret.example.json и заполните своими данными")
    
    # Проверяем опциональные переменные
    api_token = os.getenv("PACHKA_API_TOKEN")
    if not api_token:
        warnings.append("PACHKA_API_TOKEN не установлена (опционально, для отправки в конкретные чаты)")
    
    return errors, warnings

def print_help():
    """Выводит справку"""
    print("=" * 70)
    print("🤖 MRNet Bot SIMs - Запуск основного бота")
    print("=" * 70)
    print()
    print("Использование:")
    print("  python start_bot.py          # Запуск бота")
    print("  python start_bot.py --check  # Проверка конфигурации")
    print("  python start_bot.py --help   # Показать эту справку")
    print()
    print("Обязательные переменные окружения (.env):")
    print("  PACHKA_TOKEN         - Токен webhook для Pachka")
    print("  GOOGLE_SHEETS_ID     - ID таблицы Google Sheets")
    print()
    print("Опциональные переменные окружения:")
    print("  PACHKA_API_TOKEN     - API токен для отправки в конкретные чаты")
    print("  PACHKA_WEBHOOK_URL  - URL webhook (если отличается от значения по умолчанию)")
    print("  SERVER_HOST          - Хост для Flask сервера (по умолчанию 0.0.0.0)")
    print("  SERVER_PORT         - Порт для Flask сервера (по умолчанию 5000)")
    print()
    print("Необходимые файлы:")
    print("  .env                 - Переменные окружения (создайте из env.example)")
    print("  client_secret.json   - Учетные данные Google API")
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
    
    print("🤖 Запуск бота Pachka...")
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
        print("   Для справки: python start_bot.py --help")
        sys.exit(1)
    
    if warnings:
        print("⚠️  Предупреждения:")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие токена
    token = os.getenv("PACHKA_TOKEN")
    if token:
        print(f"✅ Токен найден: {token[:10]}...")
    else:
        print("❌ Ошибка: Не установлена переменная окружения PACHKA_TOKEN")
        print("📝 Создайте файл .env в корне проекта:")
        print("   PACHKA_TOKEN=ваш_токен_здесь")
        sys.exit(1)
    
    print()
    
    try:
        # Импортируем и запускаем бота
        from bot import main as bot_main
        print("🚀 Запускаем бота...")
        print()
        bot_main()
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📁 Убедитесь, что файл llms_bot_pachka/bot.py существует")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
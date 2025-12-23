#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации перед запуском бота
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def print_header():
    """Выводит заголовок"""
    print("=" * 60)
    print("🔍 Проверка конфигурации MRNet Bot SIMs")
    print("=" * 60)
    print()

def check_env_file():
    """Проверяет наличие файла .env"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Файл .env не найден!")
        print("   Создайте файл .env на основе env.example:")
        print("   cp env.example .env")
        print()
        return False
    print("✅ Файл .env найден")
    return True

def check_required_vars():
    """Проверяет обязательные переменные окружения"""
    load_dotenv()
    
    required_vars = {
        "PACHKA_TOKEN": "Токен webhook для Pachka (получите в настройках бота: Автоматизации -> Webhooks)",
        "GOOGLE_SHEETS_ID": "ID таблицы Google Sheets"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value.startswith("ваш_") or value.startswith("ВАШ_"):
            missing_vars.append((var, description))
            print(f"❌ {var} не установлена")
            print(f"   {description}")
        else:
            # Показываем только первые 10 символов для безопасности
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var} установлена ({masked_value})")
    
    print()
    return missing_vars

def check_optional_vars():
    """Проверяет опциональные переменные окружения"""
    load_dotenv()
    
    optional_vars = {
        "PACHKA_API_TOKEN": "API токен для отправки в конкретные чаты (опционально)",
        "PACHKA_WEBHOOK_URL": "URL webhook (опционально, есть значение по умолчанию)",
        "SERVER_HOST": "Хост для Flask сервера (по умолчанию 0.0.0.0)",
        "SERVER_PORT": "Порт для Flask сервера (по умолчанию 5000)"
    }
    
    print("📋 Опциональные переменные:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            if var in ["PACHKA_API_TOKEN"]:
                masked_value = value[:10] + "..." if len(value) > 10 else value
                print(f"   ✅ {var} установлена ({masked_value})")
            else:
                print(f"   ✅ {var} установлена ({value})")
        else:
            print(f"   ⚠️  {var} не установлена - {description}")
    print()

def check_google_credentials():
    """Проверяет наличие файлов Google API"""
    client_secret = Path("client_secret.json")
    client_secret_example = Path("client_secret.example.json")
    
    if not client_secret.exists():
        if client_secret_example.exists():
            print("❌ Файл client_secret.json не найден!")
            print("   Скопируйте пример и заполните своими данными:")
            print("   cp client_secret.example.json client_secret.json")
            print("   Затем получите учетные данные в Google Cloud Console")
            print()
            return False
        else:
            print("⚠️  Файлы Google API не найдены")
            print("   Создайте client_secret.json с учетными данными из Google Cloud Console")
            print()
            return False
    
    print("✅ Файл client_secret.json найден")
    return True

def check_bots_config():
    """Проверяет конфигурацию ботов (для universal_bot)"""
    bots_config = Path("bots_config.json")
    bots_config_example = Path("bots_config.example.json")
    
    if not bots_config.exists():
        if bots_config_example.exists():
            print("⚠️  Файл bots_config.json не найден (нужен для universal_bot.py)")
            print("   Скопируйте пример и заполните:")
            print("   cp bots_config.example.json bots_config.json")
            print()
            return False
        return True
    
    print("✅ Файл bots_config.json найден")
    return True

def check_dependencies():
    """Проверяет установленные зависимости"""
    print("📦 Проверка зависимостей:")
    
    required_packages = [
        "requests",
        "flask",
        "gspread",
        "google.auth",
        "pandas",
        "dotenv"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            elif package == "google.auth":
                import google.auth
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} не установлен")
            missing_packages.append(package)
    
    if missing_packages:
        print()
        print("   Установите недостающие пакеты:")
        print("   pip install -r requirements.txt")
        print()
        return False
    
    print()
    return True

def print_summary(missing_vars, env_ok, google_ok, deps_ok):
    """Выводит итоговую сводку"""
    print("=" * 60)
    print("📊 Итоговая сводка:")
    print("=" * 60)
    
    all_ok = len(missing_vars) == 0 and env_ok and google_ok and deps_ok
    
    if all_ok:
        print("✅ Все проверки пройдены! Бот готов к запуску.")
        print()
        print("Для запуска используйте:")
        print("  python start_bot.py          # Основной бот")
        print("  python start_bot2.py         # Второй бот (универсальный)")
        print("  ./scripts/run_bot.sh         # Запуск через скрипт")
        return True
    else:
        print("❌ Обнаружены проблемы. Исправьте их перед запуском:")
        print()
        
        if not env_ok:
            print("1. Создайте файл .env на основе env.example")
        
        if missing_vars:
            print("2. Заполните обязательные переменные в файле .env:")
            for var, description in missing_vars:
                print(f"   - {var}: {description}")
        
        if not google_ok:
            print("3. Настройте Google API credentials (client_secret.json)")
        
        if not deps_ok:
            print("4. Установите недостающие зависимости")
        
        print()
        print("Подробнее см. README.md и ИНСТРУКЦИЯ_ПО_ПРОЕКТУ.md")
        return False

def main():
    """Главная функция"""
    print_header()
    
    # Проверяем файл .env
    env_ok = check_env_file()
    
    # Проверяем обязательные переменные
    missing_vars = []
    if env_ok:
        missing_vars = check_required_vars()
        check_optional_vars()
    
    # Проверяем Google credentials
    google_ok = check_google_credentials()
    
    # Проверяем конфигурацию ботов
    check_bots_config()
    
    # Проверяем зависимости
    deps_ok = check_dependencies()
    
    # Выводим итоговую сводку
    success = print_summary(missing_vars, env_ok, google_ok, deps_ok)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Скрипт для диагностики проблем с ботом Pachka
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def check_environment():
    """Проверяет переменные окружения"""
    print("🔍 Проверка переменных окружения...")
    
    token = os.getenv("PACHKA_TOKEN")
    if token:
        print(f"✅ PACHKA_TOKEN найден: {token[:10]}...")
    else:
        print("❌ PACHKA_TOKEN не найден")
        return False
    
    return True

def check_bot_file():
    """Проверяет наличие файла бота"""
    print("\n📁 Проверка файлов бота...")
    
    bot_path = "llms_bot_pachka/bot.py"
    if os.path.exists(bot_path):
        print(f"✅ Файл бота найден: {bot_path}")
        return True
    else:
        print(f"❌ Файл бота не найден: {bot_path}")
        return False

def test_pachka_api():
    """Тестирует подключение к API Pachka"""
    print("\n🌐 Тестирование API Pachka...")
    
    token = os.getenv("PACHKA_TOKEN")
    if not token:
        print("❌ Токен не найден")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Тестируем базовый URL
    base_url = "https://api.pachca.com/api/shared"
    
    try:
        # Пробуем получить информацию о пользователе
        response = requests.get(f"{base_url}/users/me", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Подключение к API Pachka успешно")
            user_data = response.json()
            print(f"👤 Пользователь: {user_data.get('name', 'Неизвестно')}")
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_webhook():
    """Тестирует webhook"""
    print("\n🔗 Тестирование webhook...")
    
    webhook_url = "https://api.pachca.com/webhooks/01JXFJQRHMZR8ME5KHRY35CR05"
    
    try:
        data = {
            "message": "Тестовое сообщение от диагностики"
        }
        
        response = requests.post(webhook_url, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Webhook работает")
            return True
        else:
            print(f"❌ Ошибка webhook: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка webhook: {e}")
        return False

def check_server_status():
    """Проверяет статус сервера бота"""
    print("\n🖥️ Проверка статуса сервера...")
    
    try:
        # Проверяем, запущен ли сервер на порту 5000
        response = requests.get("http://91.196.4.149:5000", timeout=5)
        print("✅ Сервер бота запущен")
        return True
    except requests.exceptions.RequestException:
        print("❌ Сервер бота не отвечает")
        return False

def simulate_command():
    """Симулирует отправку команды /start"""
    print("\n📤 Симуляция команды /start...")
    
    try:
        # Симулируем webhook-событие
        webhook_data = {
            "type": "message",
            "event": "new",
            "content": "/start",
            "chat_id": "test_chat_id"
        }
        
        response = requests.post("http://91.196.4.149:5000/webhook", 
                               json=webhook_data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Команда /start обработана")
            return True
        else:
            print(f"❌ Ошибка обработки команды: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка отправки команды: {e}")
        return False

def main():
    print("🔧 Диагностика бота Pachka")
    print("=" * 50)
    
    # Проверяем все компоненты
    env_ok = check_environment()
    bot_file_ok = check_bot_file()
    api_ok = test_pachka_api()
    webhook_ok = test_webhook()
    server_ok = check_server_status()
    
    print("\n" + "=" * 50)
    print("📊 Результаты диагностики:")
    print(f"Переменные окружения: {'✅' if env_ok else '❌'}")
    print(f"Файл бота: {'✅' if bot_file_ok else '❌'}")
    print(f"API Pachka: {'✅' if api_ok else '❌'}")
    print(f"Webhook: {'✅' if webhook_ok else '❌'}")
    print(f"Сервер бота: {'✅' if server_ok else '❌'}")
    
    if server_ok:
        simulate_command()
    
    print("\n💡 Рекомендации:")
    if not env_ok:
        print("- Создайте файл .env с переменной PACHKA_TOKEN")
    if not bot_file_ok:
        print("- Убедитесь, что файл llms_bot_pachka/bot.py существует")
    if not api_ok:
        print("- Проверьте правильность токена PACHKA_TOKEN")
    if not webhook_ok:
        print("- Проверьте правильность webhook URL")
    if not server_ok:
        print("- Запустите бота: python start_bot.py")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Простой тест для проверки работы бота
"""

import requests
import json

def test_webhook():
    """Тестирует отправку команды /start через webhook"""
    
    # URL вашего сервера
    server_url = "http://91.196.4.149:5000"
    
    # Данные для симуляции команды /start с правильным chat_id
    webhook_data = {
        "type": "message",
        "event": "new", 
        "content": "/start",
        "chat_id": "26222583",  # Правильный ID чата
        "user_id": "user123",
        "message_id": "msg456",
        "timestamp": "2025-06-19T17:53:52Z"
    }
    
    print("🧪 Тестирование команды /start...")
    print(f"📤 Отправка данных: {json.dumps(webhook_data, ensure_ascii=False)}")
    
    try:
        # Отправляем POST запрос на webhook
        response = requests.post(f"{server_url}/webhook", 
                               json=webhook_data, 
                               timeout=10)
        
        print(f"📥 Получен ответ: {response.status_code}")
        print(f"📄 Содержимое ответа: {response.text}")
        
        if response.status_code == 200:
            print("✅ Команда /start обработана успешно!")
        else:
            print("❌ Ошибка обработки команды")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")

def test_health():
    """Тестирует доступность сервера"""
    
    server_url = "http://91.196.4.149:5000"
    
    print("🏥 Проверка здоровья сервера...")
    
    try:
        response = requests.get(f"{server_url}/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Сервер работает")
            print(f"📊 Статус: {response.json()}")
        else:
            print(f"❌ Сервер отвечает с ошибкой: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Сервер недоступен: {e}")

def test_simple_webhook():
    """Тестирует простую отправку через webhook"""
    
    print("🔗 Тестирование простого webhook сообщения...")
    
    webhook_url = "https://api.pachca.com/webhooks/01JXFJQRHMZR8ME5KHRY35CR05"
    
    data = {
        "message": "Тестовое сообщение от бота"
    }
    
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Webhook сообщение отправлено успешно")
        else:
            print(f"❌ Ошибка webhook: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка webhook: {e}")

def test_direct_message():
    """Тестирует прямую отправку сообщения в чат"""
    
    print("💬 Тестирование прямой отправки сообщения...")
    
    # URL для отправки сообщения
    url = "https://api.pachca.com/webhooks/01JXFJQRHMZR8ME5KHRY35CR05"
    
    # Получаем токен из переменной окружения
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv("PACHKA_TOKEN")
    if not token:
        print("❌ Токен не найден")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "chat_id": "26222583",
        "text": "Тестовое сообщение от бота (прямая отправка)"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"📥 Ответ API: {response.status_code}")
        if response.status_code == 200:
            print("✅ Сообщение отправлено успешно")
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    print("🤖 Тестирование бота Pachka")
    print("=" * 40)
    
    # Сначала проверяем доступность сервера
    test_health()
    print()
    
    # Тестируем простой webhook
    test_simple_webhook()
    print()
    
    # Тестируем прямую отправку сообщения
    test_direct_message()
    print()
    
    # Затем тестируем команду /start
    test_webhook() 
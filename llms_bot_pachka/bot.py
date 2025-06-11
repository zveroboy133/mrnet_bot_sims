import requests
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

class PachkaBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.pachca.com/api/shared"
        self.webhook_url = "https://api.pachca.com/webhooks/01JXFJQRHMZR8ME5KHRY35CR05"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def send_message(self, chat_id: str, text: str) -> bool:
        """
        Отправляет сообщение в указанный чат
        """
        url = f"{self.base_url}/messages/new"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        return response.status_code == 200

    def send_webhook_message(self, message: str) -> bool:
        """
        Отправляет сообщение через webhook
        """
        data = {
            "message": message
        }
        
        response = requests.post(self.webhook_url, json=data)
        return response.status_code == 200

    def process_command(self, chat_id: str, command: str) -> None:
        """
        Обрабатывает команду и отправляет результат
        """
        try:
            if command == "start":
                welcome_message = """Привет! Я бот для работы с Pachka API.
                
Доступные команды:
/start - показать это сообщение
/new [текст] - отправить новый текст через webhook

Пример использования:
/new разработка чата"""
                self.send_message(chat_id, welcome_message)
            else:
                # Отправляем команду через webhook
                if self.send_webhook_message(command):
                    self.send_message(chat_id, "Команда успешно отправлена")
                else:
                    self.send_message(chat_id, "Ошибка при отправке команды")
            
        except Exception as e:
            self.send_message(chat_id, f"Произошла ошибка: {str(e)}")

    def handle_webhook_event(self, event_data: Dict[str, Any]) -> None:
        """
        Обрабатывает входящее webhook-событие
        """
        if event_data.get("type") != "message" or event_data.get("event") != "new":
            return

        content = event_data.get("content", "")
        chat_id = event_data.get("chat_id")
        
        if not content.startswith("/"):
            return

        # Убираем слеш из начала команды
        command = content[1:]
        self.process_command(chat_id, command)

# Создаем экземпляр бота
token = os.getenv("PACHKA_TOKEN")
if not token:
    raise ValueError("Необходимо установить переменную окружения PACHKA_TOKEN")

bot = PachkaBot(token)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Обработчик входящих webhook-запросов
    """
    if request.method == 'POST':
        event_data = request.json
        bot.handle_webhook_event(event_data)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Method not allowed"}), 405

def main():
    # Отправляем тестовое сообщение через webhook
    if bot.send_webhook_message("бот работает"):
        print("Тестовое сообщение успешно отправлено")
    else:
        print("Ошибка при отправке тестового сообщения")
    
    # Запускаем Flask-сервер для обработки входящих webhook-запросов
    app.run(host='0.0.0.0', port=5000)
    
if __name__ == "__main__":
    main() 
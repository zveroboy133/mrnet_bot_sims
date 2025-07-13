import requests
import json
import os
import logging
import time
import sys
from typing import Dict, Any
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Настройка кодировки для корректного отображения русских символов
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# тест обновленной ветки
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PachkaBot:
    def __init__(self, token: str):
        self.token = token
        # Используем исходный webhook URL
        self.webhook_url = "https://api.pachca.com/webhooks/01JXFJQRHMZR8ME5KHRY35CR05"
        self.api_base_url = "https://api.pachca.com/api"
        self.last_message_time = 0
        self.min_delay = 2  # Минимальная задержка между сообщениями в секундах
        logger.info("Bot initialized")

    def send_webhook_message(self, message: str, chat_id: str = None) -> bool:
        """
        Отправляет сообщение через webhook с задержкой
        """
        # Добавляем задержку между сообщениями
        current_time = time.time()
        time_since_last = current_time - self.last_message_time
        if time_since_last < self.min_delay:
            delay = self.min_delay - time_since_last
            logger.info(f"Waiting {delay:.1f} seconds before sending message")
            time.sleep(delay)
        
        # Если указан chat_id, используем webhook с параметрами для конкретного чата
        if chat_id:
            # Используем webhook для отправки в конкретный чат
            data = {
                "message": message,
                "chat_id": chat_id
            }
            
            logger.info(f"Sending message to chat {chat_id}: {message}")
            logger.info(f"Webhook URL: {self.webhook_url}")
            logger.info(f"Data: {data}")
            
            try:
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "PachkaBot/1.0"
                }
                response = requests.post(self.webhook_url, json=data, headers=headers, timeout=10)
                self.last_message_time = time.time()
                logger.info(f"Webhook response: {response.status_code}")
                logger.info(f"Response headers: {response.headers}")
                
                if response.status_code == 200:
                    logger.info("Webhook message sent successfully to chat")
                    logger.info(f"Response content: {response.text}")
                    return True
                elif response.status_code == 429:
                    logger.warning("Rate limit reached (429), waiting 5 seconds")
                    time.sleep(5)
                    # Повторная попытка
                    response = requests.post(self.webhook_url, json=data, headers=headers, timeout=10)
                    self.last_message_time = time.time()
                    if response.status_code == 200:
                        logger.info("Webhook message sent successfully to chat after retry")
                        return True
                    else:
                        logger.error(f"Webhook error after retry: {response.status_code}")
                        return False
                else:
                    logger.error(f"Webhook error: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"Webhook exception: {e}")
                return False
        else:
            # Используем webhook для отправки в общий канал
            # Согласно документации Pachka: { "message": "Текст сообщения" }
            data = {
                "message": message
            }
            
            logger.info(f"Sending webhook message: {message}")
            logger.info(f"Webhook URL: {self.webhook_url}")
            logger.info(f"Data: {data}")
            
            try:
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "PachkaBot/1.0"
                }
                response = requests.post(self.webhook_url, json=data, headers=headers, timeout=10)
                self.last_message_time = time.time()
                logger.info(f"Webhook response: {response.status_code}")
                logger.info(f"Response headers: {response.headers}")
                
                if response.status_code == 200:
                    logger.info("Webhook message sent successfully")
                    logger.info(f"Response content: {response.text}")
                    return True
                elif response.status_code == 429:
                    logger.warning("Rate limit reached (429), waiting 5 seconds")
                    time.sleep(5)
                    # Повторная попытка
                    response = requests.post(self.webhook_url, json=data, timeout=10)
                    self.last_message_time = time.time()
                    if response.status_code == 200:
                        logger.info("Webhook message sent successfully after retry")
                        return True
                    else:
                        logger.error(f"Webhook error after retry: {response.status_code}")
                        return False
                else:
                    logger.error(f"Webhook error: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"Webhook exception: {e}")
                return False

    def send_webhook_only_message(self, message: str) -> bool:
        """
        Отправляет сообщение только через webhook (для общих уведомлений)
        """
        data = {
            "text": message
        }
        
        logger.info(f"Sending webhook only message: {message}")
        
        try:
            response = requests.post(self.webhook_url, json=data, timeout=10)
            logger.info(f"Webhook only response: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("Webhook only message sent successfully")
                logger.info(f"Response content: {response.text}")
                return True
            else:
                logger.error(f"Webhook only error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook only exception: {e}")
            return False

    def process_command(self, command: str, chat_id: str = None) -> None:
        """
        Обрабатывает команду и отправляет результат через webhook
        """
        logger.info(f"Processing command: '{command}' in chat {chat_id}")
        
        try:
            # Проверяем команду /start (слеш уже убран)
            if command.lower() == "start":
                welcome_message = """Привет! Я бот для работы с Pachka API.
                
Доступные команды:
/start - показать это сообщение
/new [текст] - отправить новый текст через webhook

Пример использования:
/new разработка чата"""
                
                logger.info("Sending welcome message")
                # Отправляем в тот же чат, откуда пришла команда
                if self.send_webhook_message(welcome_message, chat_id):
                    logger.info("Welcome message sent")
                else:
                    logger.error("Error sending welcome message")
                    
            elif command.lower().startswith("new "):
                # Команда /new
                text = command[4:].strip()  # Убираем "new " из начала
                if text:
                    logger.info(f"Sending new text via webhook: {text}")
                    if self.send_webhook_message(text, chat_id):
                        self.send_webhook_message(f"Text '{text}' sent successfully via webhook", chat_id)
                    else:
                        self.send_webhook_message("Error sending text via webhook", chat_id)
                else:
                    self.send_webhook_message("Please specify text after /new command", chat_id)
                    
            else:
                # Отправляем команду через webhook
                logger.info(f"Sending command via webhook: {command}")
                if self.send_webhook_message(command, chat_id):
                    self.send_webhook_message("Command sent successfully", chat_id)
                else:
                    self.send_webhook_message("Error sending command", chat_id)
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            self.send_webhook_message(f"An error occurred: {str(e)}")

    def handle_webhook_event(self, event_data: Dict[str, Any]) -> None:
        """
        Обрабатывает входящее webhook-событие
        """
        logger.info(f"Received webhook event: {json.dumps(event_data, ensure_ascii=False)}")
        
        # Проверяем тип события
        if event_data.get("type") != "message":
            logger.info("Event is not a message")
            return
            
        if event_data.get("event") != "new":
            logger.info("Event is not a new message")
            return

        content = event_data.get("content", "")
        chat_id = event_data.get("chat_id")
        
        logger.info(f"Content: '{content}', chat_id: {chat_id}")
        
        if not content:
            logger.info("Empty message content")
            return
        
        # Проверяем, является ли сообщение командой
        if not content.startswith("/"):
            logger.info("Message is not a command")
            return

        # Убираем слеш из начала команды
        command = content[1:].strip()
        logger.info(f"Processing command: '{command}' in chat {chat_id}")
        self.process_command(command, chat_id)

# Создаем экземпляр бота
token = os.getenv("PACHKA_TOKEN")
if not token:
    logger.error("PACHKA_TOKEN environment variable is not set")
    raise ValueError("PACHKA_TOKEN environment variable is required")

# Для отправки в конкретный чат нужен API токен
api_token = os.getenv("PACHKA_API_TOKEN")
if not api_token:
    logger.warning("PACHKA_API_TOKEN not set, using webhook token for all operations")

bot = PachkaBot(token)

@app.route('/', methods=['POST'])
def root_webhook():
    """
    Обработчик входящих webhook-запросов на корневой маршрут
    """
    if request.method == 'POST':
        try:
            event_data = request.json
            logger.info(f"Received webhook POST request on /: {json.dumps(event_data, ensure_ascii=False)}")
            
            if not event_data:
                logger.error("Empty data in webhook")
                return jsonify({"status": "error", "message": "Empty data"}), 400
                
            bot.handle_webhook_event(event_data)
            return jsonify({"status": "ok"})
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
            
    return jsonify({"status": "error", "message": "Method not allowed"}), 405

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Обработчик входящих webhook-запросов
    """
    if request.method == 'POST':
        try:
            event_data = request.json
            logger.info(f"Received webhook POST request: {json.dumps(event_data, ensure_ascii=False)}")
            
            if not event_data:
                logger.error("Empty data in webhook")
                return jsonify({"status": "error", "message": "Empty data"}), 400
                
            bot.handle_webhook_event(event_data)
            return jsonify({"status": "ok"})
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
            
    return jsonify({"status": "error", "message": "Method not allowed"}), 405

@app.route('/health', methods=['GET'])
def health_check():
    """
    Проверка здоровья сервера
    """
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

def main():
    logger.info("Starting Pachka bot (simplified version)...")
    
    # Отправляем тестовое сообщение через webhook
    logger.info("Sending test message...")
    if bot.send_webhook_message("bot is running and ready to work"):
        logger.info("Test message sent successfully")
    else:
        logger.error("Error sending test message")
    
    # Запускаем Flask-сервер для обработки входящих webhook-запросов
    logger.info("Starting Flask server on 91.217.77.71:5000")
    app.run(host='91.217.77.71', port=5000, debug=False)
    
if __name__ == "__main__":
    main() 
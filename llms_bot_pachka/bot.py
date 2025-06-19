import requests
import json
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from flask import Flask, request, jsonify

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PachkaBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.pachca.com/api/shared"
        self.webhook_url = "https://api.pachca.com/webhooks/01JXFJQRHMZR8ME5KHRY35CR05"
        self.default_chat_id = "26222583"  # Правильный ID чата
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        logger.info("Бот инициализирован")

    def send_message(self, chat_id: str, text: str) -> bool:
        """
        Отправляет сообщение в указанный чат
        """
        # Если chat_id не указан или неверный, используем дефолтный
        if not chat_id or chat_id == "test_chat_123" or chat_id == "real_chat_id_from_pachka":
            chat_id = self.default_chat_id
            logger.info(f"Используем дефолтный chat_id: {chat_id}")
        
        url = f"{self.base_url}/messages/new"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        
        logger.info(f"Отправка сообщения в чат {chat_id}: {text[:50]}...")
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            logger.info(f"Ответ API: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("Сообщение отправлено успешно")
                return True
            else:
                logger.error(f"Ошибка отправки: {response.status_code} - {response.text}")
                # Если chat_id неверный, отправляем через webhook
                if response.status_code == 404:
                    logger.info("Chat ID не найден, отправляем через webhook")
                    return self.send_webhook_message(text)
                return False
                
        except Exception as e:
            logger.error(f"Исключение при отправке: {e}")
            return False

    def send_webhook_message(self, message: str) -> bool:
        """
        Отправляет сообщение через webhook
        """
        data = {
            "message": message
        }
        
        logger.info(f"Отправка webhook сообщения: {message}")
        
        try:
            response = requests.post(self.webhook_url, json=data, timeout=10)
            logger.info(f"Webhook ответ: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("Webhook сообщение отправлено успешно")
                return True
            else:
                logger.error(f"Ошибка webhook: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Исключение webhook: {e}")
            return False

    def process_command(self, chat_id: str, command: str) -> None:
        """
        Обрабатывает команду и отправляет результат
        """
        logger.info(f"Обработка команды: '{command}' в чате {chat_id}")
        
        try:
            # Проверяем команду /start (слеш уже убран)
            if command.lower() == "start":
                welcome_message = """Привет! Я бот для работы с Pachka API.
                
Доступные команды:
/start - показать это сообщение
/new [текст] - отправить новый текст через webhook

Пример использования:
/new разработка чата"""
                
                logger.info("Отправка приветственного сообщения")
                if self.send_message(chat_id, welcome_message):
                    logger.info("Приветственное сообщение отправлено")
                else:
                    logger.error("Ошибка отправки приветственного сообщения")
                    
            elif command.lower().startswith("new "):
                # Команда /new
                text = command[4:].strip()  # Убираем "new " из начала
                if text:
                    logger.info(f"Отправка нового текста через webhook: {text}")
                    if self.send_webhook_message(text):
                        self.send_message(chat_id, f"Текст '{text}' успешно отправлен через webhook")
                    else:
                        self.send_message(chat_id, "Ошибка при отправке текста через webhook")
                else:
                    self.send_message(chat_id, "Пожалуйста, укажите текст после команды /new")
                    
            else:
                # Отправляем команду через webhook
                logger.info(f"Отправка команды через webhook: {command}")
                if self.send_webhook_message(command):
                    self.send_message(chat_id, "Команда успешно отправлена")
                else:
                    self.send_message(chat_id, "Ошибка при отправке команды")
            
        except Exception as e:
            logger.error(f"Ошибка обработки команды: {e}")
            self.send_message(chat_id, f"Произошла ошибка: {str(e)}")

    def handle_webhook_event(self, event_data: Dict[str, Any]) -> None:
        """
        Обрабатывает входящее webhook-событие
        """
        logger.info(f"Получено webhook событие: {json.dumps(event_data, ensure_ascii=False)}")
        
        # Проверяем тип события
        if event_data.get("type") != "message":
            logger.info("Событие не является сообщением")
            return
            
        if event_data.get("event") != "new":
            logger.info("Событие не является новым сообщением")
            return

        content = event_data.get("content", "")
        chat_id = event_data.get("chat_id")
        
        logger.info(f"Содержимое: '{content}', chat_id: {chat_id}")
        
        if not content:
            logger.info("Пустое содержимое сообщения")
            return
            
        if not chat_id:
            logger.info("Отсутствует chat_id, используем дефолтный")
            chat_id = self.default_chat_id
        
        # Проверяем, является ли сообщение командой
        if not content.startswith("/"):
            logger.info("Сообщение не является командой")
            return

        # Убираем слеш из начала команды
        command = content[1:].strip()
        logger.info(f"Обрабатываю команду: '{command}'")
        self.process_command(chat_id, command)

# Создаем экземпляр бота
token = os.getenv("PACHKA_TOKEN")
if not token:
    logger.error("Не установлена переменная окружения PACHKA_TOKEN")
    raise ValueError("Необходимо установить переменную окружения PACHKA_TOKEN")

bot = PachkaBot(token)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Обработчик входящих webhook-запросов
    """
    if request.method == 'POST':
        try:
            event_data = request.json
            logger.info(f"Получен webhook POST запрос: {json.dumps(event_data, ensure_ascii=False)}")
            
            if not event_data:
                logger.error("Пустые данные в webhook")
                return jsonify({"status": "error", "message": "Empty data"}), 400
                
            bot.handle_webhook_event(event_data)
            return jsonify({"status": "ok"})
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
            
    return jsonify({"status": "error", "message": "Method not allowed"}), 405

@app.route('/health', methods=['GET'])
def health_check():
    """
    Проверка здоровья сервера
    """
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

def main():
    logger.info("Запуск бота Pachka...")
    
    # Отправляем тестовое сообщение через webhook
    logger.info("Отправка тестового сообщения...")
    if bot.send_webhook_message("бот запущен и готов к работе"):
        logger.info("Тестовое сообщение успешно отправлено")
    else:
        logger.error("Ошибка при отправке тестового сообщения")
    
    # Запускаем Flask-сервер для обработки входящих webhook-запросов
    logger.info("Запуск Flask сервера на 91.196.4.149:5000")
    app.run(host='91.196.4.149', port=5000, debug=False)
    
if __name__ == "__main__":
    main() 
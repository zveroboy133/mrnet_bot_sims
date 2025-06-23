import requests
import json
import os
import logging
import time
from typing import Dict, Any
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
        self.webhook_url = "https://api.pachca.com/webhooks/01JXFJQRHMZR8ME5KHRY35CR05"
        self.api_base_url = "https://api.pachca.com/api/shared"
        self.last_message_time = 0
        self.min_delay = 2  # Минимальная задержка между сообщениями в секундах
        logger.info("Бот инициализирован")

    def send_webhook_message(self, message: str, chat_id: str = None) -> bool:
        """
        Отправляет сообщение через webhook с задержкой
        """
        # Добавляем задержку между сообщениями
        current_time = time.time()
        time_since_last = current_time - self.last_message_time
        if time_since_last < self.min_delay:
            delay = self.min_delay - time_since_last
            logger.info(f"Ожидание {delay:.1f} секунд перед отправкой сообщения")
            time.sleep(delay)
        
        # Если указан chat_id, используем API для отправки в конкретный чат
        if chat_id:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "chat_id": chat_id,
                "text": message
            }
            
            logger.info(f"Отправка сообщения в чат {chat_id}: {message}")
            
            try:
                response = requests.post(self.webhook_url, headers=headers, json=data, timeout=10)
                self.last_message_time = time.time()
                logger.info(f"API ответ: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info("Сообщение отправлено успешно в чат")
                    return True
                else:
                    logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"Исключение API: {e}")
                return False
        else:
            # Используем webhook для отправки в общий канал
            data = {
                "message": message
            }
            
            logger.info(f"Отправка webhook сообщения: {message}")
            
            try:
                response = requests.post(self.webhook_url, json=data, timeout=10)
                self.last_message_time = time.time()
                logger.info(f"Webhook ответ: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info("Webhook сообщение отправлено успешно")
                    return True
                elif response.status_code == 429:
                    logger.warning("Достигнут лимит запросов (429), ожидание 5 секунд")
                    time.sleep(5)
                    # Повторная попытка
                    response = requests.post(self.webhook_url, json=data, timeout=10)
                    self.last_message_time = time.time()
                    if response.status_code == 200:
                        logger.info("Webhook сообщение отправлено успешно после повтора")
                        return True
                    else:
                        logger.error(f"Ошибка webhook после повтора: {response.status_code}")
                        return False
                else:
                    logger.error(f"Ошибка webhook: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"Исключение webhook: {e}")
                return False

    def process_command(self, command: str, chat_id: str = None) -> None:
        """
        Обрабатывает команду и отправляет результат через webhook
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
                if self.send_webhook_message(welcome_message, chat_id):
                    logger.info("Приветственное сообщение отправлено")
                else:
                    logger.error("Ошибка отправки приветственного сообщения")
                    
            elif command.lower().startswith("new "):
                # Команда /new
                text = command[4:].strip()  # Убираем "new " из начала
                if text:
                    logger.info(f"Отправка нового текста через webhook: {text}")
                    if self.send_webhook_message(text, chat_id):
                        self.send_webhook_message(f"Текст '{text}' успешно отправлен через webhook", chat_id)
                    else:
                        self.send_webhook_message("Ошибка при отправке текста через webhook", chat_id)
                else:
                    self.send_webhook_message("Пожалуйста, укажите текст после команды /new", chat_id)
                    
            else:
                # Отправляем команду через webhook
                logger.info(f"Отправка команды через webhook: {command}")
                if self.send_webhook_message(command, chat_id):
                    self.send_webhook_message("Команда успешно отправлена", chat_id)
                else:
                    self.send_webhook_message("Ошибка при отправке команды", chat_id)
            
        except Exception as e:
            logger.error(f"Ошибка обработки команды: {e}")
            self.send_webhook_message(f"Произошла ошибка: {str(e)}", chat_id)

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
        
        # Проверяем, является ли сообщение командой
        if not content.startswith("/"):
            logger.info("Сообщение не является командой")
            return

        # Убираем слеш из начала команды
        command = content[1:].strip()
        logger.info(f"Обрабатываю команду: '{command}' в чате {chat_id}")
        self.process_command(command, chat_id)

# Создаем экземпляр бота
token = os.getenv("PACHKA_TOKEN")
if not token:
    logger.error("Не установлена переменная окружения PACHKA_TOKEN")
    raise ValueError("Необходимо установить переменную окружения PACHKA_TOKEN")

bot = PachkaBot(token)

@app.route('/', methods=['POST'])
def root_webhook():
    """
    Обработчик входящих webhook-запросов на корневой маршрут
    """
    if request.method == 'POST':
        try:
            event_data = request.json
            logger.info(f"Получен webhook POST запрос на /: {json.dumps(event_data, ensure_ascii=False)}")
            
            if not event_data:
                logger.error("Пустые данные в webhook")
                return jsonify({"status": "error", "message": "Empty data"}), 400
                
            bot.handle_webhook_event(event_data)
            return jsonify({"status": "ok"})
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
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
    logger.info("Запуск бота Pachka (упрощенная версия)...")
    
    # Отправляем тестовое сообщение через webhook
    logger.info("Отправка тестового сообщения...")
    if bot.send_webhook_message("бот запущен и готов к работе"):
        logger.info("Тестовое сообщение успешно отправлено")
    else:
        logger.error("Ошибка при отправке тестового сообщения")
    
    # Запускаем Flask-сервер для обработки входящих webhook-запросов
    logger.info("Запуск Flask сервер на 91.196.4.149:5000")
    app.run(host='91.196.4.149', port=5000, debug=False)
    
if __name__ == "__main__":
    main() 
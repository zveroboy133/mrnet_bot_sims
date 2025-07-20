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
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google_sheets_processor import GoogleSheetsProcessor

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
        
        # API токен для отправки в конкретные чаты
        self.api_token = os.getenv("PACHKA_API_TOKEN")
        if not self.api_token:
            logger.warning("PACHKA_API_TOKEN not set, will use webhook for all messages")
        else:
            logger.info(f"PACHKA_API_TOKEN found: {self.api_token[:10]}...")
        
        # Инициализируем Google Sheets процессор
        try:
            self.sheets_processor = GoogleSheetsProcessor()
            logger.info("Google Sheets processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets processor: {e}")
            self.sheets_processor = None
        
        logger.info("Bot initialized")

    def send_api_message(self, message: str, chat_id: str) -> bool:
        """
        Отправляет сообщение через API в конкретный чат
        """
        if not self.api_token:
            logger.error("API token not available for sending to specific chat")
            return False
            
        # Добавляем задержку между сообщениями
        current_time = time.time()
        time_since_last = current_time - self.last_message_time
        if time_since_last < self.min_delay:
            delay = self.min_delay - time_since_last
            logger.info(f"Waiting {delay:.1f} seconds before sending message")
            time.sleep(delay)
        
        # Попробуем разные варианты API endpoints
        url = f"{self.api_base_url}/chat.message"
        # Для API Pachka используется формат с "text"
        data = {
            "text": message,
            "chat_id": chat_id
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
            "User-Agent": "PachkaBot/1.0"
        }
        
        logger.info(f"Sending API message to chat {chat_id}: {message}")
        logger.info(f"API URL: {url}")
        logger.info(f"Data: {data}")
        
        # Если первый endpoint не работает, попробуем альтернативный
        if not self._try_api_request(url, data, headers):
            url = f"{self.api_base_url}/messages"
            logger.info(f"Trying alternative API endpoint: {url}")
            if not self._try_api_request(url, data, headers):
                logger.error("Both API endpoints failed")
                return False
        return True

    def _try_api_request(self, url: str, data: dict, headers: dict) -> bool:
        """
        Вспомогательный метод для выполнения API запроса
        """
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            self.last_message_time = time.time()
            logger.info(f"API response: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            if response.status_code == 200:
                logger.info("API message sent successfully")
                logger.info(f"Response content: {response.text}")
                return True
            elif response.status_code == 429:
                logger.warning("Rate limit reached (429), waiting 5 seconds")
                time.sleep(5)
                # Повторная попытка
                response = requests.post(url, json=data, headers=headers, timeout=10)
                self.last_message_time = time.time()
                if response.status_code == 200:
                    logger.info("API message sent successfully after retry")
                    return True
                else:
                    logger.error(f"API error after retry: {response.status_code}")
                    return False
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"API exception: {e}")
            return False

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
        
        # Если указан chat_id, используем API для отправки в конкретный чат
        if chat_id:
            logger.info(f"Using API to send message to specific chat {chat_id}")
            # Временно отключаем API для тестирования webhook fallback
            use_api = False  # Измените на True, когда настроите API токен
            if use_api and self.api_token:
                # Пытаемся отправить через API
                logger.info(f"Attempting to send via API with token: {self.api_token[:10]}...")
                if self.send_api_message(message, chat_id):
                    logger.info("API message sent successfully")
                    return True
                else:
                    logger.warning("API failed, falling back to webhook (message will go to general channel)")
                    # Fallback на webhook без chat_id (отправится в общий канал)
                    # Добавляем префикс, чтобы показать, что это ответ на команду из другого чата
                    original_message = message
                    message = f"💬 Ответ на команду из чата {chat_id}:\n{original_message}"
                    chat_id = None
                    logger.info(f"Fallback message prepared: {message[:100]}...")
            else:
                logger.warning("API token not available, falling back to webhook (message will go to general channel)")
                # Fallback на webhook без chat_id (отправится в общий канал)
                # Добавляем префикс, чтобы показать, что это ответ на команду из другого чата
                original_message = message
                message = f"💬 Ответ на команду из чата {chat_id}:\n{original_message}"
                chat_id = None
                logger.info(f"Fallback message prepared (no API token): {message[:100]}...")
        else:
            # Используем webhook для отправки в общий канал
            # ВАЖНО: НИКОГДА НЕ МЕНЯТЬ "message" на "text" - это сломает работу webhook!
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
        # ВАЖНО: НИКОГДА НЕ МЕНЯТЬ "message" на "text" - это сломает работу webhook!
        data = {
            "message": message
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

    def check_sim_activity(self, chat_id: str = None, router_name: str = None) -> None:
        """
        Проверяет активность симкарт для конкретного устройства и отправляет отчет
        """
        logger.info(f"Starting SIM card activity check for router: {router_name}")
        
        try:
            # Отправляем сообщение о начале проверки
            self.send_webhook_message(f"🔍 Начинаю проверку активности симкарт для устройства: {router_name}...", chat_id)
            
            # Проверяем, инициализирован ли Google Sheets процессор
            if not self.sheets_processor:
                error_msg = "❌ Google Sheets процессор не инициализирован. Проверьте настройки."
                self.send_webhook_message(error_msg, chat_id)
                return
            
            # Ищем данные в Google Sheets
            logger.info(f"Searching for router: {router_name} in Google Sheets")
            results = self.sheets_processor.search_by_name(router_name)
            
            if not results:
                # Устройство не найдено
                not_found_msg = f"❌ Устройство '{router_name}' не найдено в базе данных симкарт."
                self.send_webhook_message(not_found_msg, chat_id)
                return
            
            # Формируем отчет на основе найденных данных
            logger.info(f"Found {len(results)} records for router: {router_name}")
            
            # Подсчитываем статистику
            total_sims = len(results)
            active_sims = 0
            inactive_sims = 0
            low_balance_sims = 0
            
            report_lines = [f"📱 Отчет о симкартах для устройства: {router_name}\n"]
            
            for i, record in enumerate(results, 1):
                operator = record.get('2 Оператор', 'Н/Д')
                iccid = record.get('ICCID', 'Н/Д')
                status = record.get('Состояние симкарт', 'Н/Д')
                traffic = record.get('Трафик', '')
                tariff = record.get('Тариф', '')
                device = record.get('Устройство', 'Н/Д')
                
                # Определяем статус симкарты
                if 'актив' in str(status).lower():
                    status_emoji = "✅"
                    active_sims += 1
                elif 'неактив' in str(status).lower() or 'блок' in str(status).lower():
                    status_emoji = "❌"
                    inactive_sims += 1
                else:
                    status_emoji = "⚠️"
                    low_balance_sims += 1
                
                # Формируем строку для симкарты
                sim_info = f"{status_emoji} Симкарта {i}: {status_emoji} {status}"
                if traffic:
                    sim_info += f" (Трафик: {traffic})"
                elif tariff:
                    sim_info += f" (Тариф: {tariff})"
                sim_info += f" | Оператор: {operator}"
                
                report_lines.append(sim_info)
            
            # Добавляем статистику
            report_lines.append(f"\n📊 Статистика:")
            report_lines.append(f"✅ Активных: {active_sims}")
            report_lines.append(f"❌ Неактивных: {inactive_sims}")
            report_lines.append(f"⚠️ С проблемами: {low_balance_sims}")
            report_lines.append(f"📱 Всего симкарт: {total_sims}")
            report_lines.append(f"\n⏰ Проверка завершена в: {datetime.now().strftime('%H:%M:%S')}")
            
            # Отправляем отчет
            report = "\n".join(report_lines)
            self.send_webhook_message(report, chat_id)
            logger.info(f"SIM activity check completed for router: {router_name}")
            
        except Exception as e:
            error_message = f"❌ Ошибка при проверке симкарт для устройства {router_name}: {str(e)}"
            self.send_webhook_message(error_message, chat_id)
            logger.error(f"Error in check_sim_activity for router {router_name}: {e}")

    def process_command(self, command: str, chat_id: str = None) -> None:
        """
        Обрабатывает команду и отправляет результат через webhook
        """
        logger.info(f"Processing command: '{command}' in chat {chat_id}")
        logger.info(f"Command type: {type(command)}, chat_id type: {type(chat_id)}")
        
        try:
            # Проверяем команду /start (слеш уже убран)
            if command.lower() == "start":
                welcome_message = """Привет! Я бот для работы с Pachka API.
                
Доступные команды:
/start - показать это сообщение
/new [текст] - отправить новый текст через webhook
/active [устройство] - проверить активность симкарт для устройства

Пример использования:
/new разработка чата
/active router1"""
                
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
                    
            elif command.lower().startswith("active "):
                # Команда /active router_name - проверка активности симкарт для конкретного устройства
                router_name = command[7:].strip()  # Убираем "active " из начала
                
                # Извлекаем название устройства из markdown разметки [name](url)
                if router_name.startswith('[') and '](' in router_name:
                    # Извлекаем текст между [ и ]
                    start = router_name.find('[') + 1
                    end = router_name.find(']')
                    if start > 0 and end > start:
                        router_name = router_name[start:end]
                
                if router_name:
                    logger.info(f"Processing /active command for router: {router_name}")
                    self.check_sim_activity(chat_id, router_name)
                else:
                    self.send_webhook_message("Пожалуйста, укажите название устройства после /active. Пример: /active router1", chat_id)
                    
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
        logger.info(f"Full event structure: type={event_data.get('type')}, event={event_data.get('event')}, chat_id={chat_id}")
        
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
        
        # Проверяем, что chat_id не пустой
        if not chat_id:
            logger.warning("chat_id is empty, sending to general channel")
        
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
    
    try:
        # Пытаемся использовать waitress для продакшена
        from waitress import serve
        logger.info("Using waitress server for production")
        serve(app, host='91.217.77.71', port=5000, threads=4)
    except ImportError:
        logger.warning("waitress not available, using Flask development server")
        # Fallback на Flask development server
        app.run(host='91.217.77.71', port=5000, debug=False, threaded=True)
    
if __name__ == "__main__":
    main() 
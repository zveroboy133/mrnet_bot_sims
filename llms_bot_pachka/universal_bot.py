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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('universal_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class UniversalPachkaBot:
    def __init__(self, bot_config: Dict[str, Any]):
        self.config = bot_config
        self.name = bot_config.get('name', 'Unknown Bot')
        self.port = bot_config.get('port', 5000)
        self.webhook_incoming = bot_config.get('webhook_incoming')
        self.webhook_outgoing = bot_config.get('webhook_outgoing')
        self.signing_secret = bot_config.get('signing_secret')
        self.user_id = bot_config.get('user_id')
        self.access_token = bot_config.get('access_token')
        
        # API настройки
        self.api_base_url = "https://api.pachca.com"
        self.last_message_time = 0
        self.min_delay = 2  # Минимальная задержка между сообщениями в секундах
        
        # Инициализируем Google Sheets процессор
        try:
            self.sheets_processor = GoogleSheetsProcessor()
            logger.info(f"[{self.name}] Google Sheets processor initialized successfully")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to initialize Google Sheets processor: {e}")
            self.sheets_processor = None
        
        logger.info(f"[{self.name}] Bot initialized on port {self.port}")

    def send_api_message(self, message: str, chat_id: str) -> bool:
        """
        Отправляет сообщение через API в конкретный чат
        """
        if not self.access_token:
            logger.error(f"[{self.name}] Access token not available for sending to specific chat")
            return False
            
        # Добавляем задержку между сообщениями
        current_time = time.time()
        time_since_last = current_time - self.last_message_time
        if time_since_last < self.min_delay:
            delay = self.min_delay - time_since_last
            logger.info(f"[{self.name}] Waiting {delay:.1f} seconds before sending message")
            time.sleep(delay)
        
        # Используем правильный API endpoint для Pachka согласно документации
        url = f"{self.api_base_url}/messages"
        
        # Правильный формат данных согласно документации Pachka API
        data = {
            "message": {
                "entity_type": "discussion",
                "entity_id": chat_id,
                "content": message
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": f"PachkaBot/{self.name}/1.0"
        }
        
        logger.info(f"[{self.name}] Using correct Pachka API endpoint: {url}")
        logger.info(f"[{self.name}] Using correct data format: {data}")
        logger.info(f"[{self.name}] Sending API message to chat {chat_id}: {message}")
        
        # Выполняем API запрос с правильными параметрами
        return self._try_api_request(url, data, headers)

    def _try_api_request(self, url: str, data: dict, headers: dict) -> bool:
        """
        Вспомогательный метод для выполнения API запроса
        """
        logger.info(f"[{self.name}] Making API request to: {url}")
        logger.info(f"[{self.name}] Request headers: {headers}")
        logger.info(f"[{self.name}] Request data: {data}")
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            self.last_message_time = time.time()
            logger.info(f"[{self.name}] API response: {response.status_code}")
            logger.info(f"[{self.name}] Response headers: {response.headers}")
            logger.info(f"[{self.name}] Response content: {response.text}")
            
            if response.status_code == 200:
                logger.info(f"[{self.name}] API message sent successfully")
                return True
            elif response.status_code == 401:
                logger.error(f"[{self.name}] API authentication failed (401) - check access token")
                return False
            elif response.status_code == 403:
                logger.error(f"[{self.name}] API access forbidden (403) - check permissions")
                return False
            elif response.status_code == 404:
                logger.error(f"[{self.name}] API endpoint not found (404) - check URL")
                return False
            elif response.status_code == 429:
                logger.warning(f"[{self.name}] Rate limit reached (429), waiting 5 seconds")
                time.sleep(5)
                # Повторная попытка
                response = requests.post(url, json=data, headers=headers, timeout=10)
                self.last_message_time = time.time()
                if response.status_code == 200:
                    logger.info(f"[{self.name}] API message sent successfully after retry")
                    return True
                else:
                    logger.error(f"[{self.name}] API error after retry: {response.status_code}")
                    return False
            else:
                logger.error(f"[{self.name}] API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"[{self.name}] API exception: {e}")
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
            logger.info(f"[{self.name}] Waiting {delay:.1f} seconds before sending message")
            time.sleep(delay)
        
        # Если указан chat_id, используем API для отправки в конкретный чат
        if chat_id:
            logger.info(f"[{self.name}] Using API to send message to specific chat {chat_id}")
            if self.access_token:
                # Пытаемся отправить через API
                logger.info(f"[{self.name}] Attempting to send via API with token: {self.access_token[:10]}...")
                if self.send_api_message(message, chat_id):
                    logger.info(f"[{self.name}] API message sent successfully")
                    return True
                else:
                    logger.warning(f"[{self.name}] API failed, falling back to webhook (message will go to general channel)")
                    # Fallback на webhook без chat_id (отправится в общий канал)
                    # Добавляем префикс, чтобы показать, что это ответ на команду из другого чата
                    original_message = message
                    message = f"💬 Ответ на команду из чата {chat_id}:\n{original_message}"
                    chat_id = None
                    logger.info(f"[{self.name}] Fallback message prepared: {message[:100]}...")
            else:
                logger.warning(f"[{self.name}] Access token not available, falling back to webhook (message will go to general channel)")
                # Fallback на webhook без chat_id (отправится в общий канал)
                # Добавляем префикс, чтобы показать, что это ответ на команду из другого чата
                original_message = message
                message = f"💬 Ответ на команду из чата {chat_id}:\n{original_message}"
                chat_id = None
                logger.info(f"[{self.name}] Fallback message prepared (no access token): {message[:100]}...")
        
        # Отправляем сообщение через webhook (общий канал или после fallback)
        if not chat_id:
            logger.info(f"[{self.name}] Sending message via webhook to general channel")
            # Используем webhook для отправки в общий канал
            # ВАЖНО: НИКОГДА НЕ МЕНЯТЬ "message" на "text" - это сломает работу webhook!
            # Согласно документации Pachka: { "message": "Текст сообщения" }
            data = {
                "message": message
            }
            
            logger.info(f"[{self.name}] Sending webhook message: {message}")
            logger.info(f"[{self.name}] Webhook URL: {self.webhook_incoming}")
            logger.info(f"[{self.name}] Data: {data}")
            
            try:
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": f"PachkaBot/{self.name}/1.0"
                }
                response = requests.post(self.webhook_incoming, json=data, headers=headers, timeout=10)
                self.last_message_time = time.time()
                logger.info(f"[{self.name}] Webhook response: {response.status_code}")
                logger.info(f"[{self.name}] Response headers: {response.headers}")
                
                if response.status_code == 200:
                    logger.info(f"[{self.name}] Webhook message sent successfully")
                    logger.info(f"[{self.name}] Response content: {response.text}")
                    return True
                elif response.status_code == 429:
                    logger.warning(f"[{self.name}] Rate limit reached (429), waiting 5 seconds")
                    time.sleep(5)
                    # Повторная попытка
                    response = requests.post(self.webhook_incoming, json=data, timeout=10)
                    self.last_message_time = time.time()
                    if response.status_code == 200:
                        logger.info(f"[{self.name}] Webhook message sent successfully after retry")
                        return True
                    else:
                        logger.error(f"[{self.name}] Webhook error after retry: {response.status_code}")
                        return False
                else:
                    logger.error(f"[{self.name}] Webhook error: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"[{self.name}] Webhook exception: {e}")
                return False
        else:
            logger.warning(f"[{self.name}] chat_id is still set ({chat_id}), but API is disabled. Message not sent.")
            return False

    def process_command(self, command: str, chat_id: str = None) -> None:
        """
        Обрабатывает команду и отправляет результат через webhook
        """
        logger.info(f"[{self.name}] Processing command: '{command}' in chat {chat_id}")
        logger.info(f"[{self.name}] Command type: {type(command)}, chat_id type: {type(chat_id)}")
        
        try:
            # Проверяем команду /start (слеш уже убран)
            if command.lower() == "start":
                welcome_message = f"""Привет! Я {self.name} для работы с Pachka API.
                
Доступные команды:
/start - показать это сообщение
/new [текст] - отправить новый текст через webhook
/active [устройство] - проверить активность симкарт для устройства

Пример использования:
/new разработка чата
/active router1"""
                
                logger.info(f"[{self.name}] Sending welcome message")
                # Отправляем в тот же чат, откуда пришла команда
                if self.send_webhook_message(welcome_message, chat_id):
                    logger.info(f"[{self.name}] Welcome message sent")
                else:
                    logger.error(f"[{self.name}] Error sending welcome message")
                    
            elif command.lower().startswith("new "):
                # Команда /new
                text = command[4:].strip()  # Убираем "new " из начала
                if text:
                    logger.info(f"[{self.name}] Sending new text via webhook: {text}")
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
                    logger.info(f"[{self.name}] Processing /active command for router: {router_name}")
                    self.check_sim_activity(chat_id, router_name)
                else:
                    self.send_webhook_message("Пожалуйста, укажите название устройства после /active. Пример: /active router1", chat_id)
                    
            else:
                # Отправляем команду через webhook
                logger.info(f"[{self.name}] Sending command via webhook: {command}")
                if self.send_webhook_message(command, chat_id):
                    self.send_webhook_message("Command sent successfully", chat_id)
                else:
                    self.send_webhook_message("Error sending command", chat_id)
            
        except Exception as e:
            logger.error(f"[{self.name}] Error processing command: {e}")
            self.send_webhook_message(f"An error occurred: {str(e)}")

    def check_sim_activity(self, chat_id: str = None, router_name: str = None) -> None:
        """
        Проверяет активность симкарт для конкретного устройства и отправляет отчет
        """
        logger.info(f"[{self.name}] Starting SIM card activity check for router: {router_name}")
        
        try:
            # Отправляем сообщение о начале проверки
            self.send_webhook_message(f"🔍 Начинаю проверку активности симкарт для устройства: {router_name}...", chat_id)
            
            # Проверяем, инициализирован ли Google Sheets процессор
            if not self.sheets_processor:
                error_msg = "❌ Google Sheets процессор не инициализирован. Проверьте настройки."
                self.send_webhook_message(error_msg, chat_id)
                return
            
            # Ищем данные в Google Sheets
            logger.info(f"[{self.name}] Searching for router: {router_name} in Google Sheets")
            results = self.sheets_processor.search_by_name(router_name)
            
            if not results:
                # Устройство не найдено
                not_found_msg = f"❌ Устройство '{router_name}' не найдено в базе данных симкарт."
                self.send_webhook_message(not_found_msg, chat_id)
                return
            
            # Формируем отчет на основе найденных данных
            logger.info(f"[{self.name}] Found {len(results)} records for router: {router_name}")
            
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
            logger.info(f"[{self.name}] SIM activity check completed for router: {router_name}")
            
        except Exception as e:
            error_message = f"❌ Ошибка при проверке симкарт для устройства {router_name}: {str(e)}"
            self.send_webhook_message(error_message, chat_id)
            logger.error(f"[{self.name}] Error in check_sim_activity for router {router_name}: {e}")

    def handle_webhook_event(self, event_data: Dict[str, Any]) -> None:
        """
        Обрабатывает входящее webhook-событие
        """
        logger.info(f"[{self.name}] Received webhook event: {json.dumps(event_data, ensure_ascii=False)}")
        
        # Проверяем тип события
        if event_data.get("type") != "message":
            logger.info(f"[{self.name}] Event is not a message")
            return
            
        if event_data.get("event") != "new":
            logger.info(f"[{self.name}] Event is not a new message")
            return

        content = event_data.get("content", "")
        chat_id = event_data.get("chat_id")
        
        logger.info(f"[{self.name}] Content: '{content}', chat_id: {chat_id}")
        logger.info(f"[{self.name}] Full event structure: type={event_data.get('type')}, event={event_data.get('event')}, chat_id={chat_id}")
        
        if not content:
            logger.info(f"[{self.name}] Empty message content")
            return
        
        # Проверяем, является ли сообщение командой
        if not content.startswith("/"):
            logger.info(f"[{self.name}] Message is not a command")
            return

        # Убираем слеш из начала команды
        command = content[1:].strip()
        logger.info(f"[{self.name}] Processing command: '{command}' in chat {chat_id}")
        
        # Проверяем, что chat_id не пустой
        if not chat_id:
            logger.warning(f"[{self.name}] chat_id is empty, sending to general channel")
        
        self.process_command(command, chat_id)

def load_bot_config(bot_id: str) -> Dict[str, Any]:
    """
    Загружает конфигурацию бота из файла
    """
    try:
        with open('bots_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if bot_id not in config['bots']:
            raise ValueError(f"Bot '{bot_id}' not found in configuration")
        
        return config['bots'][bot_id]
    except Exception as e:
        logger.error(f"Failed to load bot configuration: {e}")
        raise

def create_bot(bot_id: str):
    """
    Создает экземпляр бота с заданной конфигурацией
    """
    config = load_bot_config(bot_id)
    return UniversalPachkaBot(config)

# Глобальная переменная для хранения экземпляра бота
bot = None

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
                
            if bot:
                bot.handle_webhook_event(event_data)
            else:
                logger.error("Bot not initialized")
                return jsonify({"status": "error", "message": "Bot not initialized"}), 500
                
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
                
            if bot:
                bot.handle_webhook_event(event_data)
            else:
                logger.error("Bot not initialized")
                return jsonify({"status": "error", "message": "Bot not initialized"}), 500
                
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
    return jsonify({
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "bot_name": bot.name if bot else "Unknown"
    })

def main():
    """
    Главная функция для запуска бота
    """
    global bot
    
    # Получаем ID бота из аргументов командной строки
    if len(sys.argv) < 2:
        print("Usage: python universal_bot.py <bot_id>")
        print("Available bots:")
        try:
            with open('bots_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                for bot_id in config['bots']:
                    print(f"  - {bot_id}: {config['bots'][bot_id]['name']}")
        except:
            print("  - Cannot load configuration")
        sys.exit(1)
    
    bot_id = sys.argv[1]
    
    try:
        # Создаем экземпляр бота
        bot = create_bot(bot_id)
        logger.info(f"Starting {bot.name} (universal version)...")
        
        # Отправляем тестовое сообщение через webhook
        logger.info("Sending test message...")
        if bot.send_webhook_message(f"Bot {bot_id} is running and ready to work"):
            logger.info("Test message sent successfully")
        else:
            logger.error("Error sending test message")
        
        # Запускаем Flask-сервер для обработки входящих webhook-запросов
        logger.info(f"Starting Flask server on 91.217.77.71:{bot.port}")
        
        try:
            # Пытаемся использовать waitress для продакшена
            from waitress import serve
            logger.info("Using waitress server for production")
            serve(app, host='91.217.77.71', port=bot.port, threads=4)
        except ImportError:
            logger.warning("waitress not available, using Flask development server")
            # Fallback на Flask development server
            app.run(host='91.217.77.71', port=bot.port, debug=False, threaded=True)
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)
    
if __name__ == "__main__":
    main() 
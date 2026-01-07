import requests
import json
import os
import logging
import time
import sys
import subprocess
import base64
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
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
        self.service_name = bot_config.get('service_name', '')
        
        # Определяем, является ли это bot3
        self.is_bot3 = (
            "bot3" in self.service_name.lower() or 
            "третий" in self.name.lower() or
            self.port == 5002
        )
        
        # Хранилище для последней ошибки скрипта
        self._last_script_error = None
        
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

    def send_api_message(self, message: str, chat_id) -> bool:
        """
        Отправляет сообщение через API в конкретный чат
        chat_id может быть строкой или числом
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
        # entity_id должен быть числом, а не строкой
        try:
            entity_id = int(chat_id) if chat_id else None
        except (ValueError, TypeError):
            logger.error(f"[{self.name}] Invalid chat_id: {chat_id}, must be a number")
            return False
        
        data = {
            "message": {
                "entity_type": "discussion",
                "entity_id": entity_id,
                "content": message
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "PachkaBot/1.0"  # Используем ASCII для избежания проблем с кодировкой
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
        
        # Если указан chat_id и это НЕ bot3, используем API для отправки в конкретный чат
        # Для bot3 по ТЗ используем только webhook (вариант A - быстрый), без API,
        # поэтому ветка с API для него отключена
        if chat_id and not self.is_bot3:
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
        # Для bot3 (вариант A) всегда отправляем через webhook, даже если передан chat_id
        if not chat_id or self.is_bot3:
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
                    "User-Agent": "PachkaBot/1.0"
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
            # Сюда попадем только для ботов, у которых API отключен и chat_id остался установлен.
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
                # Для bot3 показываем только простое приветственное сообщение
                if self.is_bot3:
                    welcome_message = f"""Привет! Я {self.name}.

Я автоматически запускаю скрипт экспорта каждый день в 17:00 MSK и отправляю файлы в Pachka.

Доступные команды:
/start - показать это сообщение
/run_script - запустить скрипт экспорта вручную"""
                else:
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
                    
            # Для bot3 обрабатываем команды
            elif self.is_bot3:
                if command.lower() == "run_script":
                    # Команда /run_script - ручной запуск ежедневной задачи
                    logger.info(f"[{self.name}] Manual script execution requested")
                    self.send_webhook_message("🔄 Запускаю скрипт экспорта...", chat_id)
                    # Запускаем задачу в отдельном потоке, чтобы не блокировать ответ
                    import threading
                    thread = threading.Thread(target=self.execute_daily_task)
                    thread.daemon = True
                    thread.start()
                else:
                    # Для bot3 все остальные команды пока не поддерживаются
                    unknown_message = f"Извините, доступные команды:\n/start - показать это сообщение\n/run_script - запустить скрипт экспорта вручную"
                    self.send_webhook_message(unknown_message, chat_id)
                    
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

    def run_iccid_imei_export_script(self) -> bool:
        """
        Запускает скрипт main.py из папки iccid_imei_export
        """
        try:
            # Определяем путь к скрипту
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_dir = os.path.join(base_dir, 'iccid_imei_export')
            script_path = os.path.join(script_dir, 'main.py')
            
            if not os.path.exists(script_path):
                logger.error(f"[{self.name}] Script not found: {script_path}")
                return False
            
            # Определяем Python из виртуального окружения или системный
            # Сначала пробуем найти виртуальное окружение в родительской папке (find_sims) - там правильные зависимости
            parent_venv = os.path.join(os.path.dirname(base_dir), 'find_sims', 'find_sims_env', 'bin', 'python')
            if os.path.exists(parent_venv):
                python_cmd = parent_venv
            else:
                # Если нет, пробуем локальное окружение
                venv_python = os.path.join(base_dir, 'find_sims_env', 'bin', 'python')
                if os.path.exists(venv_python):
                    python_cmd = venv_python
                else:
                    python_cmd = 'python3'
            
            logger.info(f"[{self.name}] Running script: {script_path}")
            logger.info(f"[{self.name}] Using Python: {python_cmd}")
            
            # Запускаем скрипт
            result = subprocess.run(
                [python_cmd, script_path],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 минут таймаут
            )
            
            if result.returncode == 0:
                logger.info(f"[{self.name}] Script executed successfully")
                if result.stdout:
                    logger.info(f"[{self.name}] Script output: {result.stdout}")
                self._last_script_error = None  # Сбрасываем ошибку при успехе
                return True
            else:
                logger.error(f"[{self.name}] Script failed with code {result.returncode}")
                if result.stdout:
                    logger.error(f"[{self.name}] Script stdout: {result.stdout}")
                if result.stderr:
                    logger.error(f"[{self.name}] Script stderr: {result.stderr}")
                # Сохраняем полную ошибку для отправки в чат
                error_details = result.stderr if result.stderr else result.stdout if result.stdout else "Неизвестная ошибка"
                self._last_script_error = error_details  # Сохраняем для использования в сообщении об ошибке
                logger.error(f"[{self.name}] Full script error: {error_details}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"[{self.name}] Script execution timeout")
            self._last_script_error = "Таймаут выполнения скрипта (превышено 5 минут)"
            return False
        except Exception as e:
            logger.error(f"[{self.name}] Error running script: {e}")
            self._last_script_error = str(e)
            return False

    def find_today_json_files(self) -> List[str]:
        """
        Находит файлы (CSV) за текущую дату в папке iccid_imei_export/exports
        Ищет файлы, которые были изменены сегодня
        Скрипт создает CSV файлы, а не JSON, но функция оставлена с прежним названием для совместимости
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_dir = os.path.join(base_dir, 'iccid_imei_export')
            exports_dir = os.path.join(script_dir, 'exports')
            
            if not os.path.exists(script_dir):
                logger.error(f"[{self.name}] Directory not found: {script_dir}")
                return []
            
            # Создаем папку exports, если её нет
            if not os.path.exists(exports_dir):
                logger.warning(f"[{self.name}] Exports directory not found, creating: {exports_dir}")
                os.makedirs(exports_dir, exist_ok=True)
            
            # Получаем текущую дату
            today = date.today()
            
            # Ищем все CSV файлы в папке exports (скрипт создает CSV, а не JSON)
            found_files = []
            
            # Ищем CSV файлы в папке exports
            for pattern in ['*.csv', '*.json']:  # Ищем и CSV, и JSON на случай изменений
                for file_path in glob.glob(os.path.join(exports_dir, pattern)):
                    try:
                        # Проверяем, что файл был изменен сегодня
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time.date() == today:
                            found_files.append(file_path)
                            logger.info(f"[{self.name}] Found today's file: {os.path.basename(file_path)} (modified: {file_time})")
                    except Exception as e:
                        logger.warning(f"[{self.name}] Error checking file {file_path}: {e}")
                        continue
            
            # Сортируем по времени изменения (новые первыми)
            found_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            logger.info(f"[{self.name}] Found {len(found_files)} files for today")
            return found_files
            
        except Exception as e:
            logger.error(f"[{self.name}] Error finding files: {e}")
            return []

    def send_files_to_pachka(self, files: List[str], chat_id: int = 26222583) -> bool:
        """
        Отправляет ссылки на файлы в Pachka
        """
        if not files:
            logger.warning(f"[{self.name}] No files to send")
            return False
        
        try:
            # Получаем IP сервера для генерации ссылок
            # Используем IP из конфигурации или из переменной окружения
            server_ip = os.getenv('SERVER_HOST', '91.217.77.71')
            if server_ip == '0.0.0.0':
                server_ip = '91.217.77.71'  # Fallback на известный IP
            
            message_parts = ["Ежедневный список iccid:imei\n"]
            
            for file_path in files:
                try:
                    file_name = os.path.basename(file_path)
                    
                    # Получаем размер файла
                    file_size = os.path.getsize(file_path)
                    
                    # Генерируем ссылку на файл
                    file_url = f"http://{server_ip}:{self.port}/files/{file_name}"
                    
                    # Добавляем ссылку в сообщение
                    message_parts.append(f"\n📄 [{file_name}]({file_url}) ({file_size} bytes)")
                    
                except Exception as e:
                    logger.error(f"[{self.name}] Error processing file {file_path}: {e}")
                    continue
            
            if len(message_parts) == 1:  # Только заголовок, файлов нет
                logger.warning(f"[{self.name}] No valid files to send")
                return False
            
            message = "\n".join(message_parts)
            
            # Отправляем сообщение
            # Для bot3 по варианту A отправляем ТОЛЬКО через webhook, без API,
            # поэтому используем send_webhook_message (даже если передан chat_id)
            return self.send_webhook_message(message, chat_id)
            
        except Exception as e:
            logger.error(f"[{self.name}] Error sending files to Pachka: {e}")
            return False

    def cleanup_old_files(self) -> None:
        """
        Удаляет старые файлы из папки exports перед созданием новых
        Файлы живут сутки или до следующего запуска скрипта
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            exports_dir = os.path.join(base_dir, 'iccid_imei_export', 'exports')
            
            if not os.path.exists(exports_dir):
                return
            
            # Удаляем все файлы из папки exports
            deleted_count = 0
            for file_name in os.listdir(exports_dir):
                file_path = os.path.join(exports_dir, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"[{self.name}] Deleted old file: {file_name}")
                except Exception as e:
                    logger.error(f"[{self.name}] Error deleting old file {file_path}: {e}")
            
            if deleted_count > 0:
                logger.info(f"[{self.name}] Cleaned up {deleted_count} old file(s) from exports directory")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error cleaning up old files: {e}")

    def execute_daily_task(self) -> None:
        """
        Выполняет ежедневную задачу: запуск скрипта, поиск файлов, отправка в Pachka
        """
        chat_id = 26222583  # ID чата для отправки (число, не строка)

        logger.info(f"[{self.name}] Starting daily task execution")
        
        try:
            # 0. Удаляем старые файлы перед созданием новых
            logger.info(f"[{self.name}] Step 0: Cleaning up old files")
            self.cleanup_old_files()
            
            # 1. Запускаем скрипт
            logger.info(f"[{self.name}] Step 1: Running export script")
            script_result = self.run_iccid_imei_export_script()
            if not script_result:
                # Получаем детали ошибки из последнего запуска скрипта
                error_msg = "❌ Ошибка: не удалось запустить скрипт экспорта"
                # Попробуем получить детали ошибки из логов (если они есть)
                # Для этого нужно сохранить последнюю ошибку в атрибуте класса
                if hasattr(self, '_last_script_error') and self._last_script_error:
                    error_msg += f"\n\nДетали ошибки:\n{self._last_script_error[:500]}"  # Ограничиваем длину
                # Вариант A: для bot3 отправляем через webhook (без API),
                # для остальных ботов оставляем API
                if self.is_bot3:
                    self.send_webhook_message(error_msg, chat_id)
                else:
                    self.send_api_message(error_msg, chat_id)
                return
            
            # 2. Ищем файлы за сегодня
            logger.info(f"[{self.name}] Step 2: Finding today's JSON files")
            files = self.find_today_json_files()
            
            if not files:
                error_msg = "❌ Ошибка: файлы не были созданы скриптом"
                if self.is_bot3:
                    self.send_webhook_message(error_msg, chat_id)
                else:
                    self.send_api_message(error_msg, chat_id)
                return
            
            # 3. Отправляем файлы в Pachka
            logger.info(f"[{self.name}] Step 3: Sending files to Pachka")
            if not self.send_files_to_pachka(files, chat_id):
                error_msg = "❌ Ошибка: не удалось отправить файлы в Pachka"
                if self.is_bot3:
                    self.send_webhook_message(error_msg, chat_id)
                else:
                    self.send_api_message(error_msg, chat_id)
                return
            
            # 4. Файлы не удаляем - они остаются для скачивания до следующего запуска
            logger.info(f"[{self.name}] Files are available for download at http://{os.getenv('SERVER_HOST', '91.217.77.71')}:{self.port}/files/")
            
            logger.info(f"[{self.name}] Daily task completed successfully")
            
        except Exception as e:
            error_msg = f"❌ Ошибка при выполнении ежедневной задачи: {str(e)}"
            logger.error(f"[{self.name}] Error in daily task: {e}")
            if self.is_bot3:
                self.send_webhook_message(error_msg, chat_id)
            else:
                self.send_api_message(error_msg, chat_id)

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
    logger.info("=== WEBHOOK ENDPOINT CALLED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request URL: {request.url}")
    
    if request.method == 'POST':
        try:
            event_data = request.json
            logger.info(f"Received webhook POST request: {json.dumps(event_data, ensure_ascii=False)}")
            
            if not event_data:
                logger.error("Empty data in webhook")
                return jsonify({"status": "error", "message": "Empty data"}), 400
                
            logger.info(f"Bot object: {bot}")
            logger.info(f"Bot type: {type(bot)}")
            
            if bot:
                logger.info("Bot is initialized, processing event...")
                bot.handle_webhook_event(event_data)
            else:
                logger.error("Bot not initialized")
                return jsonify({"status": "error", "message": "Bot not initialized"}), 500
                
            return jsonify({"status": "ok"})
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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

@app.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    """
    Раздает файлы из папки exports для скачивания
    """
    try:
        # Безопасность: проверяем, что filename не содержит опасных символов
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"status": "error", "message": "Invalid filename"}), 400
        
        # Определяем путь к файлу
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        exports_dir = os.path.join(base_dir, 'iccid_imei_export', 'exports')
        file_path = os.path.join(exports_dir, filename)
        
        # Проверяем, что файл существует и находится в правильной директории
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File not found"}), 404
        
        # Проверяем, что файл действительно в папке exports (защита от path traversal)
        if not os.path.abspath(file_path).startswith(os.path.abspath(exports_dir)):
            return jsonify({"status": "error", "message": "Access denied"}), 403
        
        # Отправляем файл
        from flask import send_file
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
        
        # Настраиваем планировщик для bot3
        if bot.is_bot3:
            try:
                scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Moscow'))
                # Запускаем задачу каждый день в 17:00 MSK
                scheduler.add_job(
                    func=bot.execute_daily_task,
                    trigger=CronTrigger(hour=17, minute=0, timezone=pytz.timezone('Europe/Moscow')),
                    id='daily_export_task',
                    name='Daily ICCID:IMEI Export',
                    replace_existing=True
                )
                scheduler.start()
                logger.info(f"[{bot.name}] Scheduler started: daily task at 17:00 MSK")
            except Exception as e:
                logger.error(f"[{bot.name}] Failed to start scheduler: {e}")
        
        # Отправляем тестовое сообщение через webhook
        logger.info("Sending test message...")
        try:
            if bot.send_webhook_message(f"Bot {bot_id} is running and ready to work"):
                logger.info("Test message sent successfully")
            else:
                logger.error("Error sending test message")
        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            logger.info("Continuing without test message...")
        
        # Запускаем Flask-сервер для обработки входящих webhook-запросов
        server_host = os.getenv('SERVER_HOST', '0.0.0.0')
        logger.info(f"Starting Flask server on {server_host}:{bot.port}")
        
        try:
            # Пытаемся использовать waitress для продакшена
            from waitress import serve
            logger.info("Using waitress server for production")
            serve(app, host=server_host, port=bot.port, threads=4)
        except ImportError:
            logger.warning("waitress not available, using Flask development server")
            # Fallback на Flask development server
            app.run(host=server_host, port=bot.port, debug=False, threaded=True)
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)
    
if __name__ == "__main__":
    main() 
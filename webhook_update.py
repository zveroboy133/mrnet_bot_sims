#!/usr/bin/env python3
"""
Webhook сервер для автоматического обновления из GitLab
Запускайте этот скрипт на сервере для получения webhook уведомлений
"""

import os
import sys
import json
import hmac
import hashlib
import subprocess
import logging
from flask import Flask, request, jsonify
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация
WEBHOOK_SECRET = os.getenv('GITLAB_WEBHOOK_SECRET', 'your-secret-key')
PROJECT_PATH = os.getenv('PROJECT_PATH', '/path/to/find_sims-main')
BRANCH = os.getenv('GITLAB_BRANCH', 'main')

def verify_signature(payload, signature):
    """Проверяет подпись webhook от GitLab"""
    if not signature:
        return False
    
    # Убираем префикс 'sha256='
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    # Вычисляем ожидаемую подпись
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def run_command(command, cwd=None):
    """Выполняет команду и возвращает результат"""
    try:
        logger.info(f"Выполняем команду: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=300  # 5 минут таймаут
        )
        
        if result.returncode == 0:
            logger.info(f"Команда выполнена успешно: {result.stdout}")
            return True, result.stdout
        else:
            logger.error(f"Ошибка выполнения команды: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error("Команда превысила таймаут")
        return False, "Timeout"
    except Exception as e:
        logger.error(f"Исключение при выполнении команды: {e}")
        return False, str(e)

def update_code():
    """Обновляет код из GitLab"""
    logger.info("🔄 Начинаем обновление кода...")
    
    # Переходим в директорию проекта
    if not os.path.exists(PROJECT_PATH):
        logger.error(f"❌ Директория проекта не найдена: {PROJECT_PATH}")
        return False
    
    # Проверяем, что это git репозиторий
    if not os.path.exists(os.path.join(PROJECT_PATH, '.git')):
        logger.error("❌ Это не git репозиторий")
        return False
    
    # Получаем последние изменения
    success, output = run_command("git fetch origin")
    if not success:
        return False
    
    # Переключаемся на нужную ветку
    success, output = run_command(f"git checkout {BRANCH}")
    if not success:
        return False
    
    # Обновляем код
    success, output = run_command(f"git pull origin {BRANCH}")
    if not success:
        return False
    
    # Запускаем деплой
    success, output = run_command("./universal_deploy.sh")
    if not success:
        return False
    
    logger.info("✅ Обновление кода завершено успешно")
    return True

@app.route('/webhook/gitlab', methods=['POST'])
def gitlab_webhook():
    """Обработчик webhook от GitLab"""
    try:
        # Получаем данные
        payload = request.get_data()
        signature = request.headers.get('X-Gitlab-Token') or request.headers.get('X-Gitlab-Signature')
        
        logger.info(f"📥 Получен webhook от GitLab: {request.headers.get('X-Gitlab-Event')}")
        
        # Проверяем подпись (если настроена)
        if WEBHOOK_SECRET != 'your-secret-key':
            if not verify_signature(payload, signature):
                logger.warning("❌ Неверная подпись webhook")
                return jsonify({'error': 'Invalid signature'}), 401
        
        # Парсим данные
        data = json.loads(payload)
        event_type = request.headers.get('X-Gitlab-Event')
        
        # Обрабатываем только push события в нужной ветке
        if event_type == 'Push Hook':
            ref = data.get('ref', '')
            if ref.endswith(f'/{BRANCH}'):
                logger.info(f"🔄 Получен push в ветку {BRANCH}, обновляем код...")
                
                # Запускаем обновление в отдельном потоке
                import threading
                thread = threading.Thread(target=update_code)
                thread.start()
                
                return jsonify({'status': 'update_started'}), 200
            else:
                logger.info(f"ℹ️ Push в ветку {ref}, игнорируем (ожидаем {BRANCH})")
                return jsonify({'status': 'ignored'}), 200
        else:
            logger.info(f"ℹ️ Игнорируем событие типа: {event_type}")
            return jsonify({'status': 'ignored'}), 200
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'project_path': PROJECT_PATH,
        'branch': BRANCH
    })

@app.route('/update', methods=['POST'])
def manual_update():
    """Ручное обновление кода"""
    try:
        logger.info("🔄 Запуск ручного обновления...")
        success = update_code()
        
        if success:
            return jsonify({'status': 'success', 'message': 'Код обновлен успешно'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Ошибка обновления кода'}), 500
            
    except Exception as e:
        logger.error(f"❌ Ошибка ручного обновления: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Запуск webhook сервера...")
    logger.info(f"📁 Путь к проекту: {PROJECT_PATH}")
    logger.info(f"🌿 Ветка: {BRANCH}")
    logger.info(f"🔗 Webhook URL: http://localhost:5000/webhook/gitlab")
    logger.info(f"💚 Health check: http://localhost:5000/health")
    logger.info(f"🔄 Ручное обновление: POST http://localhost:5000/update")
    
    app.run(host='0.0.0.0', port=5000, debug=False) 
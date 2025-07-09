#!/bin/bash

# 🚀 Универсальный скрипт настройки нового сервера для Find SIMs
# Автор: Автоматизация настройки сервера
# Версия: 1.0

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Функция для проверки, запущен ли скрипт с sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Этот скрипт должен быть запущен с правами администратора"
        echo "Используйте: sudo ./server_setup.sh"
        exit 1
    fi
}

# Функция для создания пользователя
create_user() {
    log_info "Создание нового пользователя..."
    
    read -p "Введите имя нового пользователя (по умолчанию: titkov): " username
    username=${username:-titkov}
    
    # Проверяем, существует ли пользователь
    if id "$username" &>/dev/null; then
        log_warning "Пользователь $username уже существует"
        read -p "Продолжить с существующим пользователем? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Операция отменена"
            return 1
        fi
    else
        log_info "Создаем пользователя $username..."
        adduser --gecos "" "$username"
        log_success "Пользователь $username создан"
    fi
    
    # Добавляем в группу sudo
    log_info "Добавляем пользователя $username в группу sudo..."
    usermod -aG sudo "$username"
    log_success "Пользователь $username добавлен в группу sudo"
    
    # Добавляем в группу root для полных прав
    log_info "Добавляем пользователя $username в группу root..."
    usermod -aG root "$username"
    log_success "Пользователь $username добавлен в группу root"
    
    # Настраиваем SSH ключ для пользователя
    log_info "Настройка SSH ключа для пользователя $username..."
    user_home="/home/$username"
    
    # Создаем директорию .ssh
    mkdir -p "$user_home/.ssh"
    
    # Добавляем публичный ключ
    echo "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEAprrZq2JS3+Gtbv242aNB04IMlkfIm1bahjiAI+C0KO+BXwLqY744g2CwMFfpUaKH3OjbuKqDpMBj4YTX5tL8k1u3CNTyNHoHgoIqVk2ONbqOM8Sdhqq8tQIm93Tvww509jTmKv5v7JXwlTuKebX1hLAs7PxTHJ8Y78VuXZz0Y5nEWhRol98yD8ekF2b4wHOWglGA7YKUTaF6vCdszGW6JQ35EnczosJN+XysaBvFd8GTh03+nJNQ5hXcjuURTTGXrv5VjRb6P0WKpC3RRveRQ6YQIGUUqPhN499yvEz42oTT19xqGqUnFMy7JwRs9QcpHJSQ9IkGkrtqiDcka/XB0w==" >> "$user_home/.ssh/authorized_keys"
    
    # Устанавливаем правильные права доступа
    chown -R "$username:$username" "$user_home/.ssh"
    chmod 700 "$user_home/.ssh"
    chmod 600 "$user_home/.ssh/authorized_keys"
    
    log_success "SSH ключ настроен для пользователя $username"
    
    # Сохраняем имя пользователя для использования в других функциях
    echo "$username" > /tmp/current_user.txt
}

# Функция для обновления системы
update_system() {
    log_info "Обновление системы..."
    
    read -p "Обновить систему? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        apt update
        apt upgrade -y
        log_success "Система обновлена"
    else
        log_warning "Обновление системы пропущено"
    fi
}

# Функция для установки базовых пакетов
install_basic_packages() {
    log_info "Установка базовых пакетов..."
    
    packages="curl wget git unzip python3 python3-pip python3-venv build-essential python3-dev libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 libgthread-2.0-0 libgtk-3-0 libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libjpeg-dev libpng-dev libtiff-dev libatlas-base-dev gfortran"
    
    read -p "Установить базовые пакеты ($packages)? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        apt install -y $packages
        log_success "Базовые пакеты установлены"
    else
        log_warning "Установка базовых пакетов пропущена"
    fi
}

# Функция для настройки Python окружения
setup_python_env() {
    log_info "Настройка Python окружения..."
    
    read -p "Настроить Python окружение для проекта? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f /tmp/current_user.txt ]; then
            username=$(cat /tmp/current_user.txt)
            project_dir="/home/$username/find_sims-main"
            
            # Переключаемся на пользователя для настройки окружения
            su - "$username" -c "
                if [ -d '$project_dir' ]; then
                    cd $project_dir
                    echo 'Настраиваем виртуальное окружение...'
                    python3 -m venv find_sims_env
                    source find_sims_env/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    if [ -f 'llms_bot_pachka/requirements.txt' ]; then
                        pip install -r llms_bot_pachka/requirements.txt
                    fi
                    echo 'Python окружение настроено'
                else
                    echo 'Проект не найден. Сначала клонируйте проект.'
                fi
            "
            
            log_success "Python окружение настроено"
        else
            log_error "Не удалось определить пользователя"
        fi
    else
        log_warning "Настройка Python окружения пропущена"
    fi
}

# Функция для настройки переменных окружения
setup_env_variables() {
    log_info "Настройка переменных окружения..."
    
    read -p "Настроить переменные окружения для проекта? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f /tmp/current_user.txt ]; then
            username=$(cat /tmp/current_user.txt)
            project_dir="/home/$username/find_sims-main"
            
            # Переключаемся на пользователя для настройки переменных
            su - "$username" -c "
                if [ -d '$project_dir' ]; then
                    cd $project_dir
                    echo 'Настраиваем переменные окружения...'
                    
                    # Копируем пример файла .env если он существует
                    if [ -f 'env.example' ]; then
                        cp env.example .env
                        echo 'Файл .env создан из примера'
                    fi
                    
                    # Копируем пример client_secret если он существует
                    if [ -f 'client_secret.example.json' ]; then
                        cp client_secret.example.json client_secret.json
                        echo 'Файл client_secret.json создан из примера'
                    fi
                    
                    echo 'Переменные окружения настроены'
                    echo '⚠️  Не забудьте отредактировать файлы .env и client_secret.json!'
                else
                    echo 'Проект не найден. Сначала клонируйте проект.'
                fi
            "
            
            log_success "Переменные окружения настроены"
            log_warning "⚠️  Не забудьте отредактировать файлы .env и client_secret.json!"
        else
            log_error "Не удалось определить пользователя"
        fi
    else
        log_warning "Настройка переменных окружения пропущена"
    fi
}

# Функция для настройки SSH
setup_ssh() {
    log_warning "⚠️  ВНИМАНИЕ: Настройка SSH безопасности"
    echo "Эта операция может заблокировать доступ к серверу, если настроена неправильно!"
    echo "Убедитесь, что:"
    echo "1. У вас есть доступ к серверу через другую сессию"
    echo "2. SSH ключ пользователя настроен правильно"
    echo "3. Вы знаете, что делаете"
    echo
    
    read -p "Продолжить настройку SSH безопасности? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Настройка SSH пропущена"
        return
    fi
    
    # Дополнительное подтверждение
    echo
    log_warning "⚠️  ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ"
    echo "Вы уверены, что хотите изменить настройки SSH?"
    echo "Это может заблокировать доступ к серверу!"
    echo
    
    read -p "Введите 'YES' для подтверждения: " confirmation
    if [[ "$confirmation" != "YES" ]]; then
        log_warning "Настройка SSH отменена"
        return
    fi
    
    log_info "Настройка SSH безопасности..."
    
    # Создаем резервную копию конфигурации
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    log_success "Создана резервная копия: /etc/ssh/sshd_config.backup"
    
    # Отключаем вход под root
    log_info "Отключаем вход под root..."
    sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    
    # Спрашиваем о смене порта
    echo
    read -p "Изменить SSH порт (по умолчанию 22)? Введите новый порт или нажмите Enter для пропуска: " ssh_port
    if [ ! -z "$ssh_port" ]; then
        # Проверяем, что порт является числом
        if [[ "$ssh_port" =~ ^[0-9]+$ ]] && [ "$ssh_port" -ge 1024 ] && [ "$ssh_port" -le 65535 ]; then
            sed -i "s/#Port 22/Port $ssh_port/" /etc/ssh/sshd_config
            sed -i "s/Port 22/Port $ssh_port/" /etc/ssh/sshd_config
            log_success "SSH порт изменен на $ssh_port"
            
            # Обновляем firewall для нового порта
            if command -v ufw &> /dev/null; then
                ufw allow "$ssh_port"
                log_success "Порт $ssh_port добавлен в firewall"
            fi
        else
            log_error "Неверный порт. Должен быть числом от 1024 до 65535"
            return
        fi
    fi
    
    # Проверяем конфигурацию перед перезапуском
    log_info "Проверяем конфигурацию SSH..."
    if sshd -t; then
        log_success "Конфигурация SSH корректна"
        
        # Перезапускаем SSH
        log_info "Перезапускаем SSH сервис..."
        systemctl restart ssh
        
        if systemctl is-active --quiet ssh; then
            log_success "SSH сервис успешно перезапущен"
            log_warning "⚠️  ВАЖНО: Проверьте подключение к серверу в новой сессии!"
            echo "Если подключение не работает, используйте резервную копию:"
            echo "sudo cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config"
            echo "sudo systemctl restart ssh"
        else
            log_error "Ошибка перезапуска SSH сервиса"
            log_warning "Восстанавливаем резервную копию..."
            cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
            systemctl restart ssh
        fi
    else
        log_error "Ошибка в конфигурации SSH"
        log_warning "Восстанавливаем резервную копию..."
        cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
    fi
}

# Функция для настройки firewall
setup_firewall() {
    log_info "Настройка firewall..."
    
    read -p "Настроить UFW firewall? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Устанавливаем UFW если не установлен
        if ! command -v ufw &> /dev/null; then
            apt install -y ufw
        fi
        
        # Разрешаем SSH
        ufw allow ssh
        
        # Разрешаем порт для вебхука проекта
        log_info "Разрешаем порт 5000 для вебхука проекта..."
        ufw allow 5000
        log_success "Порт 5000 открыт для вебхука"
        
        # Спрашиваем о дополнительных портах
        read -p "Разрешить HTTP (80) и HTTPS (443)? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ufw allow 80
            ufw allow 443
        fi
        
        # Включаем firewall
        ufw --force enable
        
        log_success "Firewall настроен"
    else
        log_warning "Настройка firewall пропущена"
    fi
}

# Функция для клонирования проекта
clone_project() {
    log_info "Клонирование проекта..."
    
    read -p "Клонировать проект Find SIMs? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f /tmp/current_user.txt ]; then
            username=$(cat /tmp/current_user.txt)
            project_dir="/home/$username/find_sims-main"
            
            # Переключаемся на пользователя для клонирования
            su - "$username" -c "
                if [ ! -d '$project_dir' ]; then
                    git clone https://github.com/your-repo/find_sims-main.git $project_dir
                    echo 'Проект клонирован в $project_dir'
                else
                    echo 'Проект уже существует в $project_dir'
                fi
            "
            
            log_success "Проект готов к развертыванию"
            log_info "Следующие шаги:"
            echo "1. Переключитесь на пользователя: su - $username"
            echo "2. Перейдите в проект: cd $project_dir"
            echo "3. Запустите: ./universal_deploy.sh"
        else
            log_error "Не удалось определить пользователя"
        fi
    else
        log_warning "Клонирование проекта пропущено"
    fi
}

# Функция для финальных инструкций
show_final_instructions() {
    log_success "Настройка сервера завершена!"
    echo
    echo "📋 Следующие шаги:"
    echo "1. Переключитесь на нового пользователя: su - $(cat /tmp/current_user.txt)"
    echo "2. Перейдите в проект: cd /home/$(cat /tmp/current_user.txt)/find_sims-main"
    echo "3. Активируйте виртуальное окружение: source find_sims_env/bin/activate"
    echo "4. Настройте переменные окружения:"
    echo "   - Отредактируйте файл .env (токен Pachka)"
    echo "   - Отредактируйте client_secret.json (Google API)"
    echo "5. Запустите приложение: python main.py"
    echo
    echo "🔧 Полезные команды:"
    echo "- Проверка статуса: ./check_server.sh"
    echo "- Обновление кода: ./update_code.sh"
    echo "- Настройка окружения: ./setup_env.sh"
    echo
    echo "📚 Документация:"
    echo "- README.md - общая информация"
    echo "- DEPLOYMENT.md - инструкции по развертыванию"
}

# Главная функция
main() {
    echo "🚀 Настройка нового сервера для Find SIMs"
    echo "=========================================="
    echo
    
    # Проверяем права администратора
    check_sudo
    
    # Выполняем шаги настройки
    create_user
    update_system
    install_basic_packages
    setup_firewall
    clone_project
    setup_python_env
    setup_env_variables
    setup_ssh
    
    # Показываем финальные инструкции
    show_final_instructions
    
    # Очищаем временные файлы
    rm -f /tmp/current_user.txt
}

# Запуск главной функции
main "$@" 
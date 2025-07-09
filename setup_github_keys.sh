#!/bin/bash

# 🔑 Скрипт настройки GitHub SSH ключей для пользователя titkov
# Автор: Настройка GitHub ключей
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

# Функция для проверки пользователя
check_user() {
    current_user=$(whoami)
    if [ "$current_user" != "titkov" ]; then
        log_warning "Скрипт рекомендуется запускать под пользователем titkov"
        echo "Текущий пользователь: $current_user"
        read -p "Продолжить? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Операция отменена"
            exit 0
        fi
    fi
}

# Функция для проверки git
check_git() {
    log_info "Проверка Git..."
    
    # Проверяем, установлен ли уже git
    if command -v git &> /dev/null; then
        log_success "Git установлен"
        git --version
    else
        log_error "Git не установлен"
        echo "Для установки Git обратитесь к администратору сервера"
        echo "Или установите самостоятельно:"
        echo "  sudo apt update && sudo apt install git"
        echo
        read -p "Продолжить без Git? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Операция отменена"
            exit 0
        fi
    fi
}

# Функция для настройки GitHub ключей
setup_github_keys() {
    log_info "Настройка GitHub SSH ключей..."
    
    # Определяем текущего пользователя
    username=$(whoami)
    user_home="$HOME"
    
    log_info "Создаем SSH ключи для пользователя $username..."
    
    # Проверяем, существуют ли уже ключи
    if [ -f "$user_home/.ssh/id_ed25519" ]; then
        log_warning "SSH ключи уже существуют"
        read -p "Перезаписать существующие ключи? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Операция отменена"
            return
        fi
        # Удаляем старые ключи
        rm -f "$user_home/.ssh/id_ed25519" "$user_home/.ssh/id_ed25519.pub"
    fi
    
    # Создаем директорию .ssh если её нет
    mkdir -p "$user_home/.ssh"
    chmod 700 "$user_home/.ssh"
    
    # Генерируем SSH ключи
    log_info "Генерируем SSH ключи (ed25519)..."
    ssh-keygen -t ed25519 -C "zveroboy133@gmail.com" -f "$user_home/.ssh/id_ed25519" -N ""
    
    # Устанавливаем правильные права доступа
    chmod 600 "$user_home/.ssh/id_ed25519"
    chmod 644 "$user_home/.ssh/id_ed25519.pub"
    
    log_success "SSH ключи созданы"
    
    # Показываем публичный ключ
    echo
    log_info "📋 Публичный ключ для GitHub:"
    echo "=================================="
    cat "$user_home/.ssh/id_ed25519.pub"
    echo "=================================="
    echo
    
    # Настраиваем SSH конфигурацию для GitHub
    setup_ssh_config "$username" "$user_home"
    
    # Настраиваем Git конфигурацию
    setup_git_config "$username"
    
    # Тестируем подключение к GitHub
    test_github_connection "$username"
}

# Функция для настройки SSH конфигурации
setup_ssh_config() {
    local username="$1"
    local user_home="$2"
    
    log_info "Настройка SSH конфигурации..."
    
    # Создаем или обновляем SSH конфигурацию
    cat > "$user_home/.ssh/config" << EOF
# GitHub SSH конфигурация
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
EOF
    
    # Устанавливаем права доступа
    chmod 600 "$user_home/.ssh/config"
    
    log_success "SSH конфигурация настроена"
}

# Функция для настройки Git конфигурации
setup_git_config() {
    local username="$1"
    
    log_info "Настройка Git конфигурации..."
    
    # Настраиваем Git глобально для пользователя
    git config --global user.name "titkov"
    git config --global user.email "zveroboy133@gmail.com"
    git config --global init.defaultBranch main
    git config --global pull.rebase false
    
    log_success "Git конфигурация настроена"
    
    # Показываем текущую конфигурацию
    echo
    log_info "📋 Текущая Git конфигурация:"
    git config --global --list
    echo
}

# Функция для тестирования подключения к GitHub
test_github_connection() {
    local username="$1"
    
    log_info "Тестирование подключения к GitHub..."
    
    # Тестируем SSH подключение к GitHub
    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        log_success "✅ Подключение к GitHub работает!"
    else
        log_warning "⚠️  Подключение к GitHub не работает"
        echo "Это нормально, если ключ еще не добавлен в GitHub"
        echo
        log_info "📋 Инструкции по добавлению ключа в GitHub:"
        echo "1. Скопируйте публичный ключ выше"
        echo "2. Перейдите в GitHub: Settings -> SSH and GPG keys"
        echo "3. Нажмите 'New SSH key'"
        echo "4. Вставьте ключ и сохраните"
        echo "5. Запустите этот скрипт снова для тестирования"
    fi
}

# Функция для показа инструкций
show_instructions() {
    log_success "Настройка GitHub ключей завершена!"
    echo
    echo "📋 Следующие шаги:"
    echo "1. Скопируйте публичный ключ выше"
    echo "2. Добавьте ключ в GitHub:"
    echo "   - Перейдите в GitHub: Settings -> SSH and GPG keys"
    echo "   - Нажмите 'New SSH key'"
    echo "   - Вставьте ключ и сохраните"
    echo "3. Протестируйте подключение:"
    echo "   ./setup_github_keys.sh"
    echo
    echo "🔧 Полезные команды:"
    echo "- Клонирование репозитория: git clone git@github.com:username/repo.git"
    echo "- Проверка SSH ключей: ssh-add -l"
    echo "- Тест подключения: ssh -T git@github.com"
    echo
    echo "📚 Документация:"
    echo "- GitHub SSH: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
}

# Главная функция
main() {
    echo "🔑 Настройка GitHub SSH ключей для пользователя titkov"
    echo "====================================================="
    echo
    
    # Проверяем пользователя
    check_user
    
    # Выполняем шаги настройки
    check_git
    setup_github_keys
    
    # Показываем инструкции
    show_instructions
}

# Запуск главной функции
main "$@" 
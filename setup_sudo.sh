#!/bin/bash

# 🔧 Скрипт настройки sudo для пользователя titkov
# Автор: Настройка sudo
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

# Функция для диагностики системы
diagnose_system() {
    log_info "Диагностика системы..."
    
    echo "ОС: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "Архитектура: $(uname -m)"
    echo "PATH: $PATH"
    echo "Корневая директория: $(pwd)"
    
    # Проверяем наличие основных команд
    echo "Проверка команд:"
    for cmd in usermod groups id visudo; do
        if command -v $cmd &> /dev/null; then
            echo "  ✅ $cmd: $(which $cmd)"
        elif command -v /usr/sbin/$cmd &> /dev/null; then
            echo "  ✅ $cmd: /usr/sbin/$cmd"
        elif command -v /sbin/$cmd &> /dev/null; then
            echo "  ✅ $cmd: /sbin/$cmd"
        else
            echo "  ❌ $cmd: не найден"
        fi
    done
    echo
}

# Функция для проверки, запущен ли скрипт с правами root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Этот скрипт должен быть запущен с правами root"
        echo "Варианты запуска:"
        echo "1. Переключитесь на root: su -"
        echo "2. Запустите скрипт: ./setup_sudo.sh"
        echo "3. Или попросите администратора выполнить этот скрипт"
        exit 1
    fi
}

# Функция для установки sudo
install_sudo() {
    log_info "Установка sudo..."
    
    # Проверяем, установлен ли уже sudo
    if command -v sudo &> /dev/null; then
        log_warning "sudo уже установлен"
        sudo --version
    else
        log_info "Устанавливаем sudo..."
        apt update
        apt install -y sudo
        log_success "sudo установлен"
        sudo --version
    fi
}

# Функция для настройки пользователя titkov
setup_user_sudo() {
    log_info "Настройка sudo для пользователя titkov..."
    
    # Проверяем, существует ли пользователь titkov
    if ! id "titkov" &>/dev/null; then
        log_error "Пользователь titkov не существует"
        echo "Сначала создайте пользователя с помощью server_setup.sh"
        exit 1
    fi
    
    # Добавляем пользователя в группу sudo
    log_info "Добавляем пользователя titkov в группу sudo..."
    
    # Пробуем разные варианты команды usermod
    if command -v /usr/sbin/usermod &> /dev/null; then
        /usr/sbin/usermod -aG sudo titkov
    elif command -v /sbin/usermod &> /dev/null; then
        /sbin/usermod -aG sudo titkov
    elif command -v usermod &> /dev/null; then
        usermod -aG sudo titkov
    else
        log_error "Команда usermod не найдена"
        echo "Попробуем альтернативный способ..."
        
        # Альтернативный способ через редактирование /etc/group
        if [ -f /etc/group ]; then
            log_info "Редактируем /etc/group напрямую..."
            # Создаем резервную копию
            cp /etc/group /etc/group.backup.$(date +%Y%m%d)
            
            # Добавляем пользователя в группу sudo
            sed -i 's/^sudo:.*/&,titkov/' /etc/group
            
            log_success "Пользователь titkov добавлен в группу sudo через /etc/group"
        else
            log_error "Файл /etc/group не найден"
            exit 1
        fi
    fi
    
    log_success "Пользователь titkov добавлен в группу sudo"
    
    # Проверяем настройки
    log_info "Проверяем настройки..."
    if command -v groups &> /dev/null; then
        groups titkov
    else
        echo "Группы пользователя titkov:"
        grep "^sudo:" /etc/group
    fi
}

# Функция для настройки sudoers
setup_sudoers() {
    log_info "Настройка sudoers..."
    
    # Создаем резервную копию
    cp /etc/sudoers /etc/sudoers.backup.$(date +%Y%m%d)
    log_success "Создана резервная копия: /etc/sudoers.backup.$(date +%Y%m%d)"
    
    # Проверяем, есть ли уже настройки для группы sudo
    if grep -q "^%sudo" /etc/sudoers; then
        log_warning "Группа sudo уже настроена в sudoers"
        log_info "Текущая строка sudoers для группы sudo:"
        grep "^%sudo" /etc/sudoers
    else
        log_info "Добавляем группу sudo в sudoers..."
        echo "%sudo ALL=(ALL:ALL) ALL" >> /etc/sudoers
        log_success "Группа sudo добавлена в sudoers"
        log_info "Добавленная строка: %sudo ALL=(ALL:ALL) ALL"
    fi
    
    # Проверяем конфигурацию
    log_info "Проверяем конфигурацию sudoers..."
    
    # Пробуем разные способы проверки sudoers
    if command -v visudo &> /dev/null; then
        if visudo -c; then
            log_success "Конфигурация sudoers корректна (проверено через visudo)"
        else
            log_error "Ошибка в конфигурации sudoers"
            log_warning "Восстанавливаем резервную копию..."
            cp /etc/sudoers.backup.$(date +%Y%m%d) /etc/sudoers
            exit 1
        fi
    elif command -v /usr/sbin/visudo &> /dev/null; then
        if /usr/sbin/visudo -c; then
            log_success "Конфигурация sudoers корректна (проверено через /usr/sbin/visudo)"
        else
            log_error "Ошибка в конфигурации sudoers"
            log_warning "Восстанавливаем резервную копию..."
            cp /etc/sudoers.backup.$(date +%Y%m%d) /etc/sudoers
            exit 1
        fi
    elif command -v /sbin/visudo &> /dev/null; then
        if /sbin/visudo -c; then
            log_success "Конфигурация sudoers корректна (проверено через /sbin/visudo)"
        else
            log_error "Ошибка в конфигурации sudoers"
            log_warning "Восстанавливаем резервную копию..."
            cp /etc/sudoers.backup.$(date +%Y%m%d) /etc/sudoers
            exit 1
        fi
    else
        log_warning "Команда visudo не найдена, пропускаем проверку конфигурации"
        log_info "Проверяем содержимое файла sudoers вручную..."
        
        # Простая проверка синтаксиса
        if grep -q "^%sudo" /etc/sudoers; then
            log_success "Группа sudo найдена в sudoers"
        else
            log_error "Группа sudo не найдена в sudoers"
            log_warning "Восстанавливаем резервную копию..."
            cp /etc/sudoers.backup.$(date +%Y%m%d) /etc/sudoers
            exit 1
        fi
    fi
}

# Функция для тестирования sudo
test_sudo() {
    log_info "Тестирование sudo..."
    
    # Тестируем sudo от имени пользователя titkov
    if su - titkov -c "sudo whoami" 2>/dev/null | grep -q "root"; then
        log_success "✅ sudo работает для пользователя titkov!"
    else
        log_warning "⚠️  sudo может не работать"
        echo "Попробуйте перезайти в систему или выполнить: newgrp sudo"
    fi
}

# Функция для показа инструкций
show_instructions() {
    log_success "Настройка sudo завершена!"
    echo
    echo "📋 Следующие шаги для пользователя titkov:"
    echo "1. Перезайдите в систему или выполните: newgrp sudo"
    echo "2. Протестируйте sudo: sudo whoami"
    echo "3. Теперь можете устанавливать пакеты:"
    echo "   sudo apt-get install python3-venv"
    echo
    echo "🔧 Полезные команды:"
    echo "- Установка пакетов: sudo apt-get install <пакет>"
    echo "- Обновление системы: sudo apt update && sudo apt upgrade"
    echo "- Проверка групп: groups"
    echo "- Проверка sudo: sudo -l"
    echo
    echo "⚠️  Важно:"
    echo "- Всегда используйте sudo для административных операций"
    echo "- Будьте осторожны с командами sudo"
    echo "- Не запускайте неизвестные команды с sudo"
}

# Главная функция
main() {
    echo "🔧 Настройка sudo для пользователя titkov"
    echo "========================================="
    echo
    
    # Проверяем права root
    check_root
    
    # Диагностика системы
    diagnose_system
    
    # Выполняем шаги настройки
    install_sudo
    setup_user_sudo
    setup_sudoers
    test_sudo
    
    # Показываем инструкции
    show_instructions
}

# Запуск главной функции
main "$@" 